import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  PutCommand,
  QueryCommand,
  UpdateCommand,
} from "@aws-sdk/lib-dynamodb";

const lambdaRuntime =
  globalThis.awslambda &&
  typeof globalThis.awslambda.streamifyResponse === "function"
    ? globalThis.awslambda
    : {
        streamifyResponse: (fn) => async (...args) => fn(...args),
        HttpResponseStream: {
          from() {
            return {
              write() {},
              end() {},
            };
          },
        },
      };

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const PINECONE_API_KEY = process.env.PINECONE_API_KEY || "";
const PINECONE_INDEX_HOST =
  process.env.PINECONE_INDEX_HOST ||
  "documentgpt-dev-t0mnwxg.svc.aped-4627-b74a.pinecone.io";
const DOC_TABLE = process.env.DOC_TABLE || "docgpt";

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}), {
  marshallOptions: {
    convertEmptyValues: true,
    removeUndefinedValues: true,
  },
});

const JSON_HEADERS = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
};

function chunkText(text, chunkSize = 500, overlap = 50) {
  const charsPerChunk = chunkSize * 4;
  const charsOverlap = overlap * 4;
  const chunks = [];
  let start = 0;
  while (start < text.length) {
    const end = start + charsPerChunk;
    const chunk = text.slice(start, end);
    if (chunk.trim()) {
      chunks.push({ text: chunk, start, end });
    }
    start = end - charsOverlap;
  }
  return chunks;
}

function classifyIntent(query) {
  const lower = query.toLowerCase();
  if (
    /\b(summar(y|ize|ise)|overview|abstract|gist|tl;?dr)\b/.test(lower)
  ) {
    return "summary";
  }
  if (/\b(compare|contrast|difference|similarities)\b/.test(lower)) {
    return "compare";
  }
  return "qa";
}

async function generateSummaryAndQuestions(text, docName) {
  const sample =
    text.length > 12000
      ? `${text.slice(0, 4000)}\n...\n${text.slice(
          Math.floor(text.length / 2),
          Math.floor(text.length / 2) + 2000
        )}\n...\n${text.slice(-2000)}`
      : text.slice(0, 12000);

  const payload = {
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content:
          'Return JSON {"summary":string, "questions":string[]} with 3-5 sentence summary and 3 specific questions.',
      },
      {
        role: "user",
        content: `Document: ${docName}\n\n${sample}`,
      },
    ],
    temperature: 0,
    response_format: { type: "json_object" },
  };

  const response = await callOpenAI("/chat/completions", payload);

  if (response?.choices?.length) {
    try {
      return JSON.parse(response.choices[0].message.content);
    } catch (err) {
      console.warn("Failed to parse summary JSON", err);
    }
  }

  return {
    summary: `This document (${docName}) contains ${text.length} characters. Upload successful - you can now ask questions about the content.`,
    questions: [
      "What are the main topics covered in this document?",
      "Can you summarize the key findings?",
      "What are the most important points?",
    ],
  };
}

async function callOpenAI(path, body, { stream = false } = {}) {
  if (!OPENAI_API_KEY) {
    throw new Error("Missing OPENAI_API_KEY");
  }

  const res = await fetch(`https://api.openai.com/v1${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${OPENAI_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(
      `OpenAI error (${res.status}): ${errText.slice(0, 300)}`
    );
  }

  return stream ? res : res.json();
}

async function generateEmbeddingsBatch(texts) {
  if (!texts.length) return [];
  const payload = {
    model: "text-embedding-3-large",
    input: texts.map((t) => t.slice(0, 8000)),
  };
  const response = await callOpenAI("/embeddings", payload);
  return response?.data?.map((item) => item.embedding) || [];
}

async function storeInPinecone(docId, docName, chunksWithEmbeddings) {
  if (!PINECONE_API_KEY) {
    console.warn("Pinecone not configured, skipping store");
    return false;
  }
  const vectors = chunksWithEmbeddings.map((chunk, idx) => ({
    id: `${docId}_chunk_${idx}`,
    values: chunk.embedding,
    metadata: {
      doc_id: docId,
      doc_name: docName,
      chunk_index: idx,
      text: chunk.text.slice(0, 1000),
      start_pos: chunk.start,
      end_pos: chunk.end,
    },
  }));

  const batches = [];
  const size = 100;
  for (let i = 0; i < vectors.length; i += size) {
    batches.push(vectors.slice(i, i + size));
  }

  await Promise.all(
    batches.map((batch) =>
      fetch(`https://${PINECONE_INDEX_HOST}/vectors/upsert`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Api-Key": PINECONE_API_KEY,
        },
        body: JSON.stringify({ vectors: batch }),
      })
    )
  );
  return true;
}

async function queryPinecone(query, docId, topK = 5) {
  if (!PINECONE_API_KEY) return [];
  let queryEmbedding;
  try {
    const embeddingRes = await generateEmbeddingsBatch([query]);
    queryEmbedding = embeddingRes[0];
  } catch (err) {
    console.error("Query embedding failed", err);
    return [];
  }

  const body = {
    vector: queryEmbedding,
    topK,
    includeMetadata: true,
  };
  if (docId) {
    body.filter = { doc_id: { $eq: docId } };
  }

  const res = await fetch(`https://${PINECONE_INDEX_HOST}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Api-Key": PINECONE_API_KEY,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    console.error("Pinecone query failed", await res.text());
    return [];
  }

  const data = await res.json();
  return data?.matches || [];
}

function buildCitations(matches) {
  return matches.slice(0, 5).map((match, idx) => {
    const metadata = match.metadata || {};
    const startPos = metadata.start_pos || 0;
    return {
      n: idx + 1,
      doc_id: metadata.doc_id,
      docName: metadata.doc_name || "Document",
      page: Math.floor(startPos / 3000) + 1,
      text: (metadata.text || "").slice(0, 300),
      score: match.score || 0,
    };
  });
}

function buildContextText(matches) {
  return matches
    .slice(0, 5)
    .map((match, idx) => `[${idx + 1}] ${(match.metadata?.text || "").slice(0, 1200)}`)
    .join("\n\n");
}

async function queryDynamoDocuments(userId) {
  const command = new QueryCommand({
    TableName: DOC_TABLE,
    KeyConditionExpression: "#pk = :pk AND begins_with(#sk, :doc)",
    ExpressionAttributeNames: {
      "#pk": "pk",
      "#sk": "sk",
    },
    ExpressionAttributeValues: {
      ":pk": `USER#${userId}`,
      ":doc": "DOC#",
    },
  });
  const { Items = [] } = await dynamodb.send(command);
  return Items.map((item) => ({
    doc_id: item.doc_id,
    id: item.doc_id,
    filename: item.filename,
    summary: item.summary || "",
    questions: item.questions || [],
    created_at: item.created_at,
    content: item.content || "",
    chat_history: item.chat_history || [],
  }));
}

async function saveDocumentRecord({
  userId,
  docId,
  filename,
  content,
  summary,
  questions,
}) {
  const command = new PutCommand({
    TableName: DOC_TABLE,
    Item: {
      pk: `USER#${userId}`,
      sk: `DOC#${docId}`,
      doc_id: docId,
      filename,
      content: content.slice(0, 50000),
      summary,
      questions,
      created_at: new Date().toISOString(),
    },
  });
  await dynamodb.send(command);
}

async function updateDocumentRecord({
  userId,
  docId,
  name,
  content,
  summary,
  questions,
  chatHistory,
}) {
  const expressions = [];
  const values = {};

  if (typeof name === "string") {
    expressions.push("#filename = :name");
    values[":name"] = name;
  }
  if (typeof content === "string") {
    expressions.push("#content = :content");
    values[":content"] = content.slice(0, 50000);
  }
  if (Array.isArray(questions)) {
    expressions.push("#questions = :questions");
    values[":questions"] = questions;
  }
  if (typeof summary === "string") {
    expressions.push("#summary = :summary");
    values[":summary"] = summary;
  }
  if (Array.isArray(chatHistory)) {
    expressions.push("#chat_history = :chat_history");
    values[":chat_history"] = chatHistory;
  }

  expressions.push("#updated_at = :updated");
  values[":updated"] = new Date().toISOString();

  if (!expressions.length) return;

  await dynamodb.send(
    new UpdateCommand({
      TableName: DOC_TABLE,
      Key: {
        pk: `USER#${userId}`,
        sk: `DOC#${docId}`,
      },
      UpdateExpression: `SET ${expressions.join(", ")}`,
      ExpressionAttributeNames: {
        "#filename": "filename",
        "#content": "content",
        "#summary": "summary",
        "#questions": "questions",
        "#chat_history": "chat_history",
        "#updated_at": "updated_at",
      },
      ExpressionAttributeValues: values,
    })
  );
}

function createStream(responseStream, { statusCode = 200, headers = {} }) {
  return lambdaRuntime.HttpResponseStream.from(responseStream, {
    statusCode,
    headers: {
      ...JSON_HEADERS,
      ...headers,
    },
  });
}

function writeJson(responseStream, statusCode, payload, headers = {}) {
  const stream = createStream(responseStream, {
    statusCode,
    headers,
  });
  stream.write(JSON.stringify(payload));
  stream.end();
}

function parseEvent(event) {
  const context = event.requestContext || {};
  const httpCtx = context.http || {};
  const method = httpCtx.method || event.httpMethod || "GET";
  const path =
    event.rawPath ||
    httpCtx.path ||
    event.path ||
    "/";
  const query =
    event.queryStringParameters ||
    event.rawQueryString ||
    {};

  let rawBody = event.body;
  if (rawBody && event.isBase64Encoded) {
    rawBody = Buffer.from(rawBody, "base64").toString("utf8");
  }

  let body = rawBody;
  if (typeof rawBody === "string") {
    try {
      body = JSON.parse(rawBody);
    } catch {
      body = rawBody;
    }
  }

  return {
    method: method.toUpperCase(),
    path,
    body,
    rawBody: rawBody || "",
    headers: event.headers || {},
    query:
      typeof query === "string"
        ? Object.fromEntries(new URLSearchParams(query))
        : query,
  };
}

async function openAiChatWithContext({
  query,
  contextMatches,
  stream,
  responseStream,
}) {
  if (!contextMatches.length) {
    writeJson(
      responseStream,
      200,
      {
        response:
          "I couldn't find relevant passages in your documents. The document may not have been vectorized yet.",
        citations: [],
        context_used: 0,
      }
    );
    return;
  }

  const contextText = buildContextText(contextMatches);
  const citations = buildCitations(contextMatches);

  const payload = {
    model: "gpt-4o-mini",
    temperature: 0,
    max_tokens: 500,
    stream,
    messages: [
      {
        role: "system",
        content:
          "Use ONLY EVIDENCE sections. Every factual sentence must end with [n]. If unsupported by evidence, say you can't find it in the document.",
      },
      {
        role: "user",
        content: `EVIDENCE:\n${contextText}\n\nQUESTION: ${query}\nANSWER:`,
      },
    ],
  };

  if (stream) {
    const httpStream = createStream(responseStream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
    await streamOpenAIResponse(payload, httpStream, citations);
    return;
  }

  const response = await callOpenAI("/chat/completions", payload);
  const answer = response?.choices?.[0]?.message?.content;

  if (!answer) {
    writeJson(
      responseStream,
      500,
      { error: "No response from OpenAI" }
    );
    return;
  }

  if (!/\[\d+\]/.test(answer)) {
    writeJson(responseStream, 200, {
      response: "I can't find support for that in the document.",
      citations: [],
      context_used: contextMatches.length,
    });
    return;
  }

  writeJson(responseStream, 200, {
    response: answer,
    citations,
    context_used: contextMatches.length,
  });
}

async function streamOpenAIResponse(payload, httpStream, citations) {
  try {
    const res = await callOpenAI("/chat/completions", payload, {
      stream: true,
    });
    const decoder = new TextDecoder();
    let buffer = "";
    httpStream.write(
      `data: ${JSON.stringify({ event: "metadata", citations })}\n\n`
    );

    for await (const chunk of res.body) {
      buffer += decoder.decode(chunk, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payloadStr = line.replace("data: ", "").trim();
        if (payloadStr === "[DONE]") continue;
        try {
          const parsed = JSON.parse(payloadStr);
          const token = parsed?.choices?.[0]?.delta?.content;
          if (token) {
            httpStream.write(
              `data: ${JSON.stringify({ token, citations })}\n\n`
            );
          }
        } catch (err) {
          console.warn("Failed to parse stream chunk", err);
        }
      }
    }
    httpStream.write("data: [DONE]\n\n");
    httpStream.end();
  } catch (err) {
    console.error("Streaming error", err);
    httpStream.write(
      `data: ${JSON.stringify({
        error: "Streaming failed. Please try again.",
      })}\n\n`
    );
    httpStream.write("data: [DONE]\n\n");
    httpStream.end();
  }
}

export const handler = lambdaRuntime.streamifyResponse(
  async (event, responseStream) => {
    const req = parseEvent(event);
    const { method, path } = req;

    if (method === "OPTIONS") {
      writeJson(responseStream, 200, { ok: true });
      return;
    }

    if (method === "GET" && path === "/dev/health") {
      writeJson(responseStream, 200, {
        status: "healthy",
        environment: "dev",
        rag_enabled: Boolean(PINECONE_API_KEY),
        runtime: "node",
        timestamp: new Date().toISOString(),
      });
      return;
    }

    if (method === "POST" && path === "/dev/upload") {
      const body = req.body || {};
      const userId = body.user_id || "guest_dev";
      const filename = body.filename;
      const content = body.content;

      if (!filename || !content) {
        writeJson(responseStream, 400, {
          error: "Missing filename or content",
        });
        return;
      }

      const docId = `doc_${Date.now()}`;

      let summaryData;
      try {
        summaryData = await generateSummaryAndQuestions(content, filename);
      } catch (err) {
        console.error("Summary failed", err);
        summaryData = {
          summary: `Document uploaded successfully. You can now ask questions about ${filename}.`,
          questions: [
            "What is this document about?",
            "What are the main points?",
            "Can you summarize the key findings?",
          ],
        };
      }

      const chunks = chunkText(content);
      const limitedChunks = chunks.slice(0, 200);
      const chunksWithEmbeddings = [];
      const batchSize = 10;
      for (let i = 0; i < limitedChunks.length; i += batchSize) {
        const batch = limitedChunks.slice(i, i + batchSize);
        try {
          const embeddings = await generateEmbeddingsBatch(
            batch.map((c) => c.text)
          );
          embeddings.forEach((embedding, idx) =>
            chunksWithEmbeddings.push({
              ...batch[idx],
              embedding,
            })
          );
        } catch (err) {
          console.error("Batch embedding failed", err);
        }
      }

      if (chunksWithEmbeddings.length) {
        await storeInPinecone(docId, filename, chunksWithEmbeddings);
      }

      await saveDocumentRecord({
        userId,
        docId,
        filename,
        content,
        summary: summaryData.summary,
        questions: summaryData.questions,
      });

      writeJson(responseStream, 200, {
        message: "Document uploaded",
        doc_id: docId,
        artifact: {
          doc_id: docId,
          summary: summaryData.summary,
          questions: summaryData.questions,
        },
      });
      return;
    }

    if (path === "/documents" && method === "GET") {
      const userId = req.query?.user_id;
      if (!userId) {
        writeJson(responseStream, 400, {
          error: "Missing user_id",
        });
        return;
      }
      try {
        const documents = await queryDynamoDocuments(userId);
        writeJson(responseStream, 200, { documents });
      } catch (err) {
        console.error("Dynamo query failed", err);
        writeJson(responseStream, 500, { documents: [] });
      }
      return;
    }

    if (path === "/documents" && method === "POST") {
      const body = req.body || {};
      const userId = body.user_id;
      const docId = body.doc_id;
      if (!userId || !docId) {
        writeJson(responseStream, 400, {
          error: "Missing user_id or doc_id",
        });
        return;
      }
      await updateDocumentRecord({
        userId,
        docId,
        name: body.name,
        content: body.content,
        summary: body.summary,
        questions: body.questions,
        chatHistory: body.chat_history,
      });
      writeJson(responseStream, 200, { message: "Saved" });
      return;
    }

    if (method === "POST" && path === "/dev/chat") {
      const body = req.body || {};
      const query =
        body.query ||
        body.messages?.[body.messages.length - 1]?.content ||
        "";
      const stream = Boolean(body.stream);
      if (!query) {
        writeJson(responseStream, 400, { error: "No query provided" });
        return;
      }
      const intent = classifyIntent(query);

      if (intent === "summary" && body.docPreview) {
        try {
          const summaryData = await generateSummaryAndQuestions(
            body.docPreview.slice(0, 12000),
            "This document"
          );
          writeJson(responseStream, 200, {
            response: summaryData.summary,
            previewQuestions: summaryData.questions,
            citations: [],
          });
          return;
        } catch (err) {
          console.error("Preview summary failed", err);
        }
      }

      const docId = body.doc_id || body.documentId;
      const matches = await queryPinecone(query, docId, 8);
      await openAiChatWithContext({
        query,
        contextMatches: matches,
        stream,
        responseStream,
      });
      return;
    }

    writeJson(responseStream, 404, { error: "Endpoint not found" });
  }
);

export const helpers = {
  chunkText,
  classifyIntent,
  buildCitations,
};
