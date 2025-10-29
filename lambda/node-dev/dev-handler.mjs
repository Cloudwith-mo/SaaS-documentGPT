import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  PutCommand,
  QueryCommand,
  UpdateCommand,
  GetCommand,
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
const ALLOWED_ORIGINS = (
  process.env.ALLOWED_ORIGINS || "https://documentgpt.io"
)
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);
if (ALLOWED_ORIGINS.length > 1 && ALLOWED_ORIGINS.includes("*")) {
  for (let i = ALLOWED_ORIGINS.length - 1; i >= 0; i -= 1) {
    if (ALLOWED_ORIGINS[i] === "*") ALLOWED_ORIGINS.splice(i, 1);
  }
}

const MAX_CHAT_MESSAGES = Number(process.env.MAX_CHAT_MESSAGES || 50);

const dynamodb = DynamoDBDocumentClient.from(new DynamoDBClient({}), {
  marshallOptions: {
    convertEmptyValues: true,
    removeUndefinedValues: true,
  },
});

function buildCorsHeaders(
  requestHeaders = {},
  contentType = "application/json"
) {
  const requestOrigin = requestHeaders.origin || requestHeaders.Origin;
  let origin = "*";

  if (ALLOWED_ORIGINS.length) {
    if (requestOrigin && ALLOWED_ORIGINS.includes(requestOrigin)) {
      origin = requestOrigin;
    } else {
      origin = ALLOWED_ORIGINS[0];
    }
  } else if (requestOrigin) {
    origin = requestOrigin;
  }

  const headers = {
    "Content-Type": contentType,
    "Access-Control-Allow-Headers":
      "Content-Type,Authorization,X-Requested-With",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Origin": origin,
    Vary: "Origin",
  };

  if (origin !== "*") {
    headers["Access-Control-Allow-Credentials"] = "true";
  }

  return headers;
}

function normalizePath(path = "/") {
  if (!path) return "/";
  const parts = path.split("/").filter(Boolean);
  if (parts.length && ["dev", "prod", "stage", "staging"].includes(parts[0])) {
    return parts.length === 1 ? "/" : `/${parts.slice(1).join("/")}`;
  }
  return path.startsWith("/") ? path : `/${path}`;
}

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

const EMBEDDING_MODEL =
  process.env.OPENAI_EMBED_MODEL || "text-embedding-3-small";

async function generateEmbeddingsBatch(texts) {
  if (!texts.length) return [];
  const payload = {
    model: EMBEDDING_MODEL,
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
    batches.map(async (batch) => {
      const res = await fetch(`https://${PINECONE_INDEX_HOST}/vectors/upsert`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Api-Key": PINECONE_API_KEY,
        },
        body: JSON.stringify({ vectors: batch }),
      });

      if (!res.ok) {
        const details = await res.text();
        throw new Error(
          `Pinecone upsert failed (${res.status}): ${details.slice(0, 200)}`
        );
      }
    })
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

function formatChatHistory(chatHistory = [], limit = 6) {
  return chatHistory
    .slice(-limit)
    .map((turn) => {
      const role = turn.sender === "bot" ? "Assistant" : "User";
      const text = typeof turn.text === "string" ? turn.text : "";
      return `${role}: ${text.replace(/\s+/g, " ").trim()}`.slice(0, 500);
    })
    .filter(Boolean)
    .join("\n");
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
    updated_at: item.updated_at,
    last_message_preview: item.last_message_preview || "",
    last_message_at: item.last_message_at,
  }));
}

async function getDocumentItem(userId, docId) {
  const command = new GetCommand({
    TableName: DOC_TABLE,
    Key: {
      pk: `USER#${userId}`,
      sk: `DOC#${docId}`,
    },
  });
  const { Item = null } = await dynamodb.send(command);
  return Item;
}

async function getDocumentChatHistory(userId, docId) {
  const item = await getDocumentItem(userId, docId);
  if (!item) return [];
  if (!Array.isArray(item.chat_history)) return [];
  return item.chat_history.slice(-MAX_CHAT_MESSAGES);
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
      updated_at: new Date().toISOString(),
      chat_history: [],
      last_message_preview: "",
      last_message_at: null,
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
    const trimmedHistory = chatHistory.slice(-MAX_CHAT_MESSAGES);
    expressions.push("#chat_history = :chat_history");
    values[":chat_history"] = trimmedHistory;

    const lastTurn = trimmedHistory[trimmedHistory.length - 1];
    expressions.push("#last_message_preview = :last_message_preview");
    expressions.push("#last_message_at = :last_message_at");
    values[":last_message_preview"] = lastTurn?.text
      ? String(lastTurn.text).slice(0, 280)
      : "";
    values[":last_message_at"] =
      lastTurn?.created_at ||
      lastTurn?.timestamp ||
      (lastTurn ? new Date().toISOString() : null);
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
        "#last_message_preview": "last_message_preview",
        "#last_message_at": "last_message_at",
      },
      ExpressionAttributeValues: values,
    })
  );
}

function createStream(responseStream, { statusCode = 200, headers = {} }) {
  return lambdaRuntime.HttpResponseStream.from(responseStream, {
    statusCode,
    headers,
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
  respond,
  streamHeaders,
  chatHistoryText = "",
  docName = "",
  docSummary = "",
}) {
  if (!contextMatches.length) {
    respond(200, {
      response:
        "I couldn't find relevant passages in your documents. The document may not have been vectorized yet.",
      citations: [],
      context_used: 0,
    });
    return;
  }

  const contextText = buildContextText(contextMatches);
  const citations = buildCitations(contextMatches);
  const systemPromptParts = [
    "Use ONLY EVIDENCE sections. Every factual sentence must end with [n]. If unsupported by evidence, say you can't find it in the document.",
  ];
  if (docName) {
    systemPromptParts.push(`Document title: ${docName}`);
  }
  if (docSummary) {
    systemPromptParts.push(
      `Document summary (for orientation only): ${docSummary.slice(0, 600)}`
    );
  }

  const promptSegments = [`EVIDENCE:\n${contextText}`];
  if (chatHistoryText) {
    promptSegments.push(`CONVERSATION HISTORY:\n${chatHistoryText}`);
  }
  promptSegments.push(`QUESTION: ${query}`);
  promptSegments.push("ANSWER:");

  const payload = {
    model: "gpt-4o-mini",
    temperature: 0,
    max_tokens: 500,
    stream,
    messages: [
      {
        role: "system",
        content: systemPromptParts.join("\n"),
      },
      {
        role: "user",
        content: promptSegments.join("\n\n"),
      },
    ],
  };

  if (stream) {
    const httpStream = createStream(responseStream, {
      headers: streamHeaders,
    });
    await streamOpenAIResponse(payload, httpStream, citations);
    return;
  }

  const response = await callOpenAI("/chat/completions", payload);
  const answer = response?.choices?.[0]?.message?.content;

  if (!answer) {
    respond(500, { error: "No response from OpenAI" });
    return;
  }

  if (!/\[\d+\]/.test(answer)) {
    respond(200, {
      response: "I can't find support for that in the document.",
      citations: [],
      context_used: contextMatches.length,
    });
    return;
  }

  respond(200, {
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
    const normalizedPath = normalizePath(path);
    const corsJsonHeaders = buildCorsHeaders(req.headers);
    const streamHeaders = {
      ...buildCorsHeaders(req.headers, "text/event-stream"),
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    };
    const respond = (status, payload, headers = corsJsonHeaders) =>
      writeJson(responseStream, status, payload, headers);

    if (method === "OPTIONS") {
      respond(200, { ok: true });
      return;
    }

    if (method === "GET" && (normalizedPath === "/health" || normalizedPath === "/dev/health")) {
      respond(200, {
        status: "healthy",
        environment: "dev",
        rag_enabled: Boolean(PINECONE_API_KEY),
        runtime: "node",
        timestamp: new Date().toISOString(),
      });
      return;
    }

    if (method === "POST" && normalizedPath === "/upload") {
      const body = req.body || {};
      const userId = body.user_id || "guest_dev";
      const filename = body.filename;
      const content = body.content;

      if (!filename || !content) {
        respond(400, {
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
        try {
          await storeInPinecone(docId, filename, chunksWithEmbeddings);
        } catch (err) {
          console.error("Pinecone store failed", err);
          respond(502, {
            error:
              "Document indexing failed: Pinecone returned an error while storing embeddings.",
          });
          return;
        }
      }

      await saveDocumentRecord({
        userId,
        docId,
        filename,
        content,
        summary: summaryData.summary,
        questions: summaryData.questions,
      });

      respond(200, {
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

    if (method === "GET" && normalizedPath === "/usage") {
      const userId = req.query?.user_id || "guest_dev";
      const usage = {
        chats_used: 0,
        documents_uploaded: 0,
      };
      respond(200, {
        plan: "Free",
        usage,
        limits: {
          chats: Number(process.env.DEV_CHAT_LIMIT || 10),
          documents: Number(process.env.DEV_DOC_LIMIT || 2),
        },
        user_id: userId,
      });
      return;
    }

    if (method === "GET" && normalizedPath === "/documents") {
      const userId = req.query?.user_id;
      if (!userId) {
        respond(400, {
          error: "Missing user_id",
        });
        return;
      }
      try {
        const documents = await queryDynamoDocuments(userId);
        respond(200, { documents });
      } catch (err) {
        console.error("Dynamo query failed", err);
        respond(500, { documents: [] });
      }
      return;
    }

    if (
      method === "GET" &&
      normalizedPath.startsWith("/documents/") &&
      normalizedPath.endsWith("/chat")
    ) {
      const segments = normalizedPath.split("/").filter(Boolean);
      if (segments.length !== 3) {
        respond(404, { error: "Invalid chat path" });
        return;
      }
      const docId = decodeURIComponent(segments[1]);
      const userId = req.query?.user_id;
      if (!userId) {
        respond(400, { error: "Missing user_id" });
        return;
      }
      try {
        const item = await getDocumentItem(userId, docId);
        if (!item) {
          respond(404, { error: "Document not found" });
          return;
        }
        const history = Array.isArray(item.chat_history)
          ? item.chat_history.slice(-MAX_CHAT_MESSAGES)
          : [];
        respond(200, {
          doc_id: docId,
          chat_history: history,
          last_message_preview: item.last_message_preview || "",
          last_message_at: item.last_message_at || null,
        });
      } catch (err) {
        console.error("Chat history fetch failed", err);
        respond(500, { error: "Failed to load chat history" });
      }
      return;
    }

    if (method === "POST" && normalizedPath === "/documents") {
      const body = req.body || {};
      const userId = body.user_id;
      const docId = body.doc_id;
      if (!userId || !docId) {
        respond(400, {
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
      respond(200, { message: "Saved" });
      return;
    }

    if (method === "POST" && normalizedPath === "/chat") {
      const body = req.body || {};
      const query =
        body.query ||
        body.messages?.[body.messages.length - 1]?.content ||
        "";
      const stream = Boolean(body.stream);
      if (!query) {
        respond(400, { error: "No query provided" });
        return;
      }
      const userId = body.user_id || req.query?.user_id || "guest_dev";
      const intent = classifyIntent(query);

      if (intent === "summary" && body.docPreview) {
        try {
          const summaryData = await generateSummaryAndQuestions(
            body.docPreview.slice(0, 12000),
            "This document"
          );
          respond(200, {
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
      let docItem = null;
      let historySource = [];
      if (docId && userId) {
        try {
          docItem = await getDocumentItem(userId, docId);
          historySource = Array.isArray(docItem?.chat_history)
            ? docItem.chat_history
            : [];
        } catch (err) {
          console.warn("Failed to load stored chat history", err);
        }
      }
      if (Array.isArray(body.chat_history) && body.chat_history.length) {
        historySource = body.chat_history;
      }
      const chatHistoryText = formatChatHistory(historySource);

      console.log(
        `[chat] user=${userId} doc=${docId || "none"} history_turns=${
          historySource.length
        } query="${query.slice(0, 120)}"`
      );

      const matches = await queryPinecone(query, docId, 8);
      console.log(
        `[chat] pinecone matches=${matches.length} doc=${docId || "none"}`
      );

      await openAiChatWithContext({
        query,
        contextMatches: matches,
        stream,
        responseStream,
        respond,
        streamHeaders,
        chatHistoryText,
        docName: docItem?.filename || body.doc_name || "",
        docSummary: docItem?.summary || "",
      });
      return;
    }

    respond(404, { error: "Endpoint not found" });
  }
);

export const helpers = {
  chunkText,
  classifyIntent,
  buildCitations,
};
