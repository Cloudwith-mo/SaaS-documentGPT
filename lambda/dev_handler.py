"""
DocumentGPT Dev Handler - LangGraph Orchestration + MCP-style Tooling
"""
import base64
import json
import mimetypes
import os
import re
import traceback
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from statistics import mean
from typing import Optional, Sequence, Tuple

import boto3

import requests
from boto3.dynamodb.conditions import Key
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage

from agents import DEFAULT_RESEARCH_SYSTEM_PROMPT, build_langgraph_agent, web_search
from config import get_settings, make_cors_headers
from knowledge_graph import (
    compute_doc_relationships,
    entities_to_document_payload,
    format_document_entities,
    format_entity_detail,
    format_user_entities,
    run_entity_extraction,
)

# Environment
settings = get_settings()
OPENAI_API_KEY = settings.openai_api_key
PINECONE_API_KEY = settings.pinecone_api_key
PINECONE_INDEX_NAME = settings.pinecone_index or 'documentgpt-dev'
PINECONE_INDEX_HOST = settings.pinecone_index_host
DOC_TABLE = settings.doc_table
MEDIA_BUCKET = settings.media_bucket
MEDIA_QUEUE_URL = settings.media_queue_url
WIKI_MAX_SECTIONS = 12

# Ensure Pinecone cache can write inside Lambda /tmp filesystem
os.environ["HOME"] = "/tmp"
os.environ["PINECONE_CACHE_DIR"] = "/tmp/pinecone"
os.environ["XDG_CACHE_HOME"] = "/tmp/.cache"
os.environ["XDG_CONFIG_HOME"] = "/tmp/.config"
os.makedirs("/tmp/.cache", exist_ok=True)
os.makedirs("/tmp/.config", exist_ok=True)
os.makedirs(os.environ["PINECONE_CACHE_DIR"], exist_ok=True)

# AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

# LangChain setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)

# Pinecone REST helpers
def pinecone_request(path, payload):
    if not PINECONE_INDEX_HOST:
        raise RuntimeError("PINECONE_INDEX_HOST not configured")

    url = f"https://{PINECONE_INDEX_HOST}{path}"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": PINECONE_API_KEY,
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as request_error:
        raise RuntimeError(f"Pinecone request failed: {request_error}") from request_error

    if not response.ok:
        raise RuntimeError(
            f"Pinecone request failed ({response.status_code}): {response.text[:300]}"
        )
    return response.json()


def pinecone_upsert(vectors):
    if not vectors:
        return

    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = {"vectors": vectors[i : i + batch_size]}
        pinecone_request("/vectors/upsert", batch)


def pinecone_query(vector, doc_id=None, top_k=5):
    body = {
        "vector": vector,
        "topK": top_k,
        "includeMetadata": True,
    }
    if doc_id:
        body["filter"] = {"doc_id": {"$eq": doc_id}}
    data = pinecone_request("/query", body)
    return data.get("matches", [])

# Text splitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj == obj.to_integral_value():
                return int(obj)
            return float(obj)
        return super().default(obj)

def make_headers(content_type='application/json', request_headers=None):
    return make_cors_headers(
        settings,
        request_headers=request_headers,
        content_type=content_type,
        add_origin_header=True,
    )

# MCP-style Tools
def pinecone_retrieve(query: str, doc_id: str = None) -> str:
    """Retrieve relevant document chunks from Pinecone vector database"""
    try:
        query_embedding = embeddings.embed_query(query)
        results = pinecone_query(query_embedding, doc_id=doc_id, top_k=5)

        if not results:
            return "No relevant passages found in documents."

        passages = []
        for idx, match in enumerate(results):
            metadata = match.get("metadata") or {}
            text = metadata.get("text") or ""
            if not text:
                continue
            passages.append(f"[{idx + 1}] {text}")

        if not passages:
            return "No relevant passages found in documents."

        context = "\n\n".join(passages)
        return f"RELEVANT PASSAGES:\n{context}"
    except Exception as e:
        print(f"⚠️ Pinecone retrieve error: {e}")
        traceback.print_exc()
        return "Error retrieving from vector database."

# Define tools (mutable list so we can swap document filter per-request)
tools = [
    Tool(
        name="document_search",
        func=lambda q: pinecone_retrieve(q),
        description="Search user's uploaded documents for relevant information. Use this FIRST for any question about documents.",
    ),
    Tool(
        name="web_search",
        func=web_search,
        description="Search the web for current information or facts not in documents. Use ONLY if document_search returns no results.",
    ),
]

RESEARCH_SYSTEM_PROMPT = DEFAULT_RESEARCH_SYSTEM_PROMPT

research_agent = build_langgraph_agent(llm, RESEARCH_SYSTEM_PROMPT, tools)

def extract_pdf_text(content):
    """Extract text from PDF content"""
    try:
        import PyPDF2
        import io
        pdf_file = io.BytesIO(content.encode('latin-1') if isinstance(content, str) else content)
        reader = PyPDF2.PdfReader(pdf_file)
        return "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        print(f"⚠️ PDF extraction failed: {e}")
        return content

def generate_summary(text, doc_name):
    """Generate document summary using LLM"""
    try:
        prompt = f"Summarize this document in 3-5 sentences:\n\n{text[:8000]}"
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"⚠️ Summary generation failed: {e}")
        return f"Document {doc_name} uploaded successfully."


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
HIGHLIGHT_KEYWORDS = {
    "action": {"review", "schedule", "follow-up", "deadline", "email", "meet", "deliver", "plan", "todo", "decide"},
    "date": {"today", "tomorrow", "week", "month", "quarter", "january", "february", "march", "april", "may", "june",
             "july", "august", "september", "october", "november", "december", "monday", "tuesday", "wednesday",
             "thursday", "friday", "saturday", "sunday", "deadline", "due", "by "},
}

POSITIVE_WORDS = {
    "accomplished", "amazing", "awesome", "calm", "confident", "excited", "grateful", "great", "happy", "hopeful",
    "optimistic", "proud", "relaxed", "renewed", "satisfied", "strong", "successful", "thrilled", "victory", "win",
}
NEGATIVE_WORDS = {
    "angry", "anxious", "awful", "burnout", "concerned", "depressed", "doubt", "exhausted", "frustrated", "lost",
    "nervous", "overwhelmed", "sad", "stressed", "tired", "uncertain", "upset", "worried",
}
EMOTION_KEYWORDS = {
    "joy": {"grateful", "happy", "joy", "excited", "delighted", "pleased"},
    "anger": {"angry", "frustrated", "mad", "irritated"},
    "sadness": {"sad", "down", "depressed", "unhappy"},
    "fear": {"scared", "afraid", "worried", "anxious"},
    "surprise": {"surprised", "shocked", "amazed"},
}
STOPWORDS = {
    "the", "and", "or", "with", "about", "your", "from", "into", "that", "this", "have", "been", "will", "for", "are",
    "was", "were", "been", "being", "after", "before", "when", "while", "over", "under", "again", "today", "yesterday",
    "tomorrow", "project", "tasks", "task", "note", "notes",
}

ANALYTICS_TTL_HOURS = 6


def generate_highlights(text: str, max_count: int = 12) -> list[dict]:
    """Generate structured highlight snippets from document text without additional LLM calls."""
    if not text:
        return []

    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    segments = SENTENCE_SPLIT_RE.split(normalized)
    highlights = []
    cursor = 0
    max_length = len(normalized)

    for segment in segments:
        raw = segment.strip()
        if not raw:
            cursor += len(segment) + 1
            continue

        start_idx = normalized.find(segment, cursor)
        if start_idx == -1:
            start_idx = cursor
        cursor = start_idx + len(segment)

        length = len(raw)
        if length < 40 or length > 320:
            continue

        lower = raw.lower()
        keyword_hits = {kind for kind, keywords in HIGHLIGHT_KEYWORDS.items()
                        if any(keyword in lower for keyword in keywords)}
        kind = "key"
        if "action" in keyword_hits:
            kind = "action"
        elif "date" in keyword_hits:
            kind = "important"

        density_score = min(1.0, length / 180)
        punctuation_bonus = 0.25 if ":" in raw or ";" in raw else 0.0
        keyword_bonus = min(0.35, len(keyword_hits) * 0.2)
        capital_bonus = 0.1 if raw[:1].isupper() else 0.0
        score = density_score + punctuation_bonus + keyword_bonus + capital_bonus

        context_start = max(0, start_idx - 80)
        context_end = min(max_length, start_idx + length + 80)
        context_snippet = normalized[context_start:context_end].strip()

        highlights.append({
            "id": f"hl-{uuid.uuid4().hex[:8]}",
            "text": raw,
            "kind": kind,
            "offset": start_idx,
            "length": length,
            "score": round(score, 4),
            "context": context_snippet,
        })

    if not highlights:
        return []

    highlights.sort(key=lambda h: h["score"], reverse=True)
    seen = set()
    deduped = []
    for highlight in highlights:
        key = highlight["text"].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(highlight)
        if len(deduped) >= max_count:
            break

    return deduped


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(tz=None)
    except Exception:
        return None


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    return [tok for tok in tokens if tok not in STOPWORDS and len(tok) > 2]


def _extract_topics(item: dict) -> list[str]:
    topics: list[str] = []
    entities = item.get("entities") or []
    for entity in entities:
        name = entity.get("name")
        if name and isinstance(name, str):
            topics.append(name.strip())
    if not topics:
        summary = item.get("summary") or item.get("content") or ""
        counts = Counter(_tokenize(summary))
        topics = [word.title() for word, _ in counts.most_common(5)]
    return topics[:5]


def _estimate_sentiment(text: str) -> tuple[float, str]:
    if not text:
        return 0.0, "neutral"
    lowered = text.lower()
    tokens = _tokenize(lowered)
    if not tokens:
        return 0.0, "neutral"
    pos_hits = sum(1 for token in tokens if token in POSITIVE_WORDS)
    neg_hits = sum(1 for token in tokens if token in NEGATIVE_WORDS)
    score = (pos_hits - neg_hits) / max(1, pos_hits + neg_hits)
    if pos_hits == neg_hits == 0:
        score = 0.0
    dominant_emotion = "neutral"
    max_emotion_hits = 0
    for emotion, keywords in EMOTION_KEYWORDS.items():
        hits = sum(1 for token in tokens if token in keywords)
        if hits > max_emotion_hits:
            max_emotion_hits = hits
            dominant_emotion = emotion
    if max_emotion_hits == 0:
        dominant_emotion = "joy" if score > 0.4 else "sadness" if score < -0.4 else "neutral"
    return round(score, 4), dominant_emotion


def _moving_average(series: Sequence[float], window: int = 7) -> list[Optional[float]]:
    results: list[Optional[float]] = []
    values: list[float] = []
    for idx, value in enumerate(series):
        values.append(value)
        start = max(0, idx - window + 1)
        window_slice = values[start : idx + 1]
        try:
            avg = mean(window_slice)
            results.append(round(avg, 4))
        except Exception:
            results.append(None)
    return results


def _generate_predictive_insights(sentiment_ma: list[Optional[float]], velocity_points: list[dict], topics_by_month: list[dict]) -> list[str]:
    insights: list[str] = []
    if sentiment_ma:
        latest = next((val for val in reversed(sentiment_ma) if val is not None), None)
        earlier = next((val for val in reversed(sentiment_ma[:-7]) if val is not None), None)
        if latest is not None and earlier is not None:
            delta = latest - earlier
            if delta <= -0.15:
                insights.append("Sentiment has trended downward over the past week. Consider reviewing recent stressors.")
            elif delta >= 0.15:
                insights.append("Sentiment is improving week-over-week. Keep reinforcing the habits that are working.")
    if velocity_points:
        recent_words = sum(point["words"] for point in velocity_points[-7:])
        prior_words = sum(point["words"] for point in velocity_points[-14:-7])
        if prior_words and recent_words < prior_words * 0.7:
            insights.append("Writing velocity dropped more than 30% this week. A gentle reminder to journal could help.")
        elif prior_words and recent_words > prior_words * 1.2:
            insights.append("Writing output increased significantly this week. Capture that momentum with structured goals.")
    if topics_by_month:
        last_month = topics_by_month[-1]
        if len(topics_by_month) >= 2:
            prev_month = topics_by_month[-2]
            last_topics = {topic["topic"] for topic in last_month["topics"]}
            prev_topics = {topic["topic"] for topic in prev_month["topics"]}
            new_topics = last_topics - prev_topics
            if new_topics:
                insights.append(f"New focus areas emerging: {', '.join(sorted(new_topics))}. Explore whether they align with your goals.")
    if not insights:
        insights.append("Keep journaling consistently to uncover deeper trends.")
    return insights[:4]


def _prepare_doc_entities(raw_entities):
    """Convert entity payload ready for DynamoDB storage."""
    doc_entities = []
    for entity in raw_entities:
        doc_entities.append(
            {
                'entity_id': entity['entity_id'],
                'name': entity['name'],
                'type': entity['type'],
                'salience': Decimal(str(entity['salience'])),
                'mentions': entity.get('mentions', []),
            }
        )
    return doc_entities


def _upsert_knowledge_graph(table, user_id, doc_id, doc_entities):
    """Persist entity aggregates and document edges for the knowledge graph."""
    if not doc_entities:
        return

    now_iso = datetime.now().isoformat()
    for entity in doc_entities:
        user_pk = f'USER#{user_id}'
        entity_sk = f'ENTITY#{entity["entity_id"]}'
        key = {'pk': user_pk, 'sk': entity_sk}

        existing_resp = table.get_item(Key=key)
        existing = existing_resp.get('Item') if isinstance(existing_resp, dict) else None
        doc_ids = set(existing.get('doc_ids', [])) if existing else set()
        doc_ids.add(doc_id)

        mentions = existing.get('mentions', []) if existing else []
        for mention in entity.get('mentions', []):
            if mention and mention not in mentions and len(mentions) < 10:
                mentions.append(mention)

        created_at = existing.get('created_at') if existing else now_iso

        table.put_item(Item={
            'pk': user_pk,
            'sk': entity_sk,
            'entity_id': entity['entity_id'],
            'entity_name': entity['name'],
            'entity_type': entity['type'],
            'doc_ids': sorted(doc_ids),
            'doc_count': Decimal(str(len(doc_ids))),
            'mentions': mentions,
            'salience': entity['salience'],
            'created_at': created_at,
            'updated_at': now_iso,
            'last_seen_doc_id': doc_id,
        })

        table.put_item(Item={
            'pk': f'DOC#{doc_id}',
            'sk': f'ENTITY#{entity["entity_id"]}',
            'doc_id': doc_id,
            'entity_id': entity['entity_id'],
            'entity_name': entity['name'],
            'entity_type': entity['type'],
            'salience': entity['salience'],
            'mentions': entity.get('mentions', []),
            'user_id': user_id,
            'updated_at': now_iso,
        })


def _list_user_entities(table, user_id):
    resp = table.query(
        KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('ENTITY#')
    )
    return format_user_entities(resp.get('Items', []))


def _get_document_entities(table, doc_id):
    resp = table.query(
        KeyConditionExpression=Key('pk').eq(f'DOC#{doc_id}') & Key('sk').begins_with('ENTITY#')
    )
    return format_document_entities(resp.get('Items', []))


def _fetch_document_metadata(table, user_id, doc_ids):
    doc_items = []
    for doc_id in doc_ids:
        response = table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'})
        item = response.get('Item') if isinstance(response, dict) else None
        if item:
            doc_items.append(item)
    return doc_items


def _get_entity_detail_payload(table, user_id, entity_id):
    response = table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'ENTITY#{entity_id}'})
    entity_item = response.get('Item') if isinstance(response, dict) else None
    if not entity_item:
        return None

    doc_ids = entity_item.get('doc_ids', []) or []
    doc_items = _fetch_document_metadata(table, user_id, doc_ids)
    return format_entity_detail(entity_item, doc_items)


def _decimal_or_none(value: Optional[float]):
    if value is None:
        return None
    try:
        return Decimal(str(round(value, 6)))
    except Exception:
        return None


def _build_week_key(date_obj: datetime) -> str:
    iso_year, iso_week, _ = date_obj.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _compute_temporal_analytics(table, user_id: str, force: bool = False):
    analytics_key = {'pk': f'USER#{user_id}', 'sk': 'ANALYTICS#TEMPORAL'}
    existing_resp = table.get_item(Key=analytics_key)
    existing_item = existing_resp.get('Item') if isinstance(existing_resp, dict) else None
    if existing_item and not force:
        generated_at = _parse_datetime(existing_item.get('generated_at'))
        if generated_at and datetime.now().astimezone(tz=None) - generated_at < timedelta(hours=ANALYTICS_TTL_HOURS):
            payload = existing_item.get('payload')
            if isinstance(payload, str):
                try:
                    data = json.loads(payload)
                    data['generated_at'] = existing_item.get('generated_at')
                    return data
                except json.JSONDecodeError:
                    pass

    docs_resp = table.query(
        KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('DOC#')
    )
    documents = docs_resp.get('Items', [])

    monthly_topics_counter: dict[str, Counter] = defaultdict(Counter)
    daily_stats: dict[datetime, dict] = {}

    for item in documents:
        created_at = _parse_datetime(item.get('created_at') or item.get('updated_at'))
        if not created_at:
            continue
        month_key = created_at.strftime("%Y-%m")
        for topic in _extract_topics(item):
            monthly_topics_counter[month_key][topic] += 1

        content = item.get('content') or item.get('summary') or ''
        sentiment, emotion = _estimate_sentiment(content)
        word_count = len(_tokenize(content))
        day_key = created_at.replace(hour=0, minute=0, second=0, microsecond=0)
        stats = daily_stats.setdefault(day_key, {"sentiments": [], "emotions": Counter(), "words": 0, "entries": 0})
        stats["sentiments"].append(sentiment)
        stats["emotions"][emotion] += 1
        stats["words"] += word_count
        stats["entries"] += 1

    monthly_topics = []
    for month in sorted(monthly_topics_counter.keys()):
        counter = monthly_topics_counter[month]
        top_topics = [{"topic": topic, "count": int(count)} for topic, count in counter.most_common(5)]
        monthly_topics.append({"month": month, "topics": top_topics})

    timeline = []
    sorted_days = sorted(daily_stats.keys())
    for day in sorted_days:
        data = daily_stats[day]
        avg_sentiment = mean(data["sentiments"]) if data["sentiments"] else 0.0
        dominant_emotion = data["emotions"].most_common(1)[0][0] if data["emotions"] else "neutral"
        timeline.append({
            "date": day.date().isoformat(),
            "sentiment": round(avg_sentiment, 4),
            "emotion": dominant_emotion,
            "words": data["words"],
        })
    moving_average_values = _moving_average([point["sentiment"] for point in timeline], window=7) if timeline else []
    for point, ma_value in zip(timeline, moving_average_values):
        point["moving_average"] = ma_value

    weekly_totals: dict[str, int] = defaultdict(int)
    for day in sorted_days:
        week_key = _build_week_key(day)
        weekly_totals[week_key] += daily_stats[day]["words"]
    weekly_velocity = [{"week": week, "words": words} for week, words in sorted(weekly_totals.items())]

    streak = 0
    best_streak = 0
    last_day = None
    for day in sorted_days:
        if daily_stats[day]["words"] > 0:
            if last_day and (day - last_day).days == 1:
                streak += 1
            else:
                streak = 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
        last_day = day

    words_last_7_days = sum(daily_stats[day]["words"] for day in sorted_days if (sorted_days[-1] - day).days < 7) if sorted_days else 0
    words_prev_7_days = sum(
        daily_stats[day]["words"]
        for day in sorted_days
        if 7 <= (sorted_days[-1] - day).days < 14
    ) if len(sorted_days) > 7 else 0

    insights = _generate_predictive_insights(moving_average_values, [{"words": daily_stats[day]["words"]} for day in sorted_days], monthly_topics)

    payload = {
        'user_id': user_id,
        'generated_at': datetime.now().astimezone(tz=None).isoformat(),
        'monthly_topics': monthly_topics,
        'sentiment_timeline': timeline,
        'velocity': {
            'daily_average_words': round(mean(point["words"] for point in timeline), 2) if timeline else 0,
            'weekly_totals': weekly_velocity,
            'streak_days': best_streak,
            'words_last_7_days': words_last_7_days,
            'words_prev_7_days': words_prev_7_days,
        },
        'insights': insights,
    }

    table.put_item(Item={
        'pk': f'USER#{user_id}',
        'sk': 'ANALYTICS#TEMPORAL',
        'user_id': user_id,
        'generated_at': payload['generated_at'],
        'payload': json.dumps(payload),
    })
    return payload


def _list_wiki_pages(table, user_id: str):
    resp = table.query(
        KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('WIKI#')
    )
    return resp.get('Items', [])


def _get_wiki_page(table, user_id: str, page_id: str):
    resp = table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'WIKI#{page_id}'})
    return resp.get('Item') if isinstance(resp, dict) else None


def _sanitize_sections(sections: Sequence[dict]) -> Tuple[list, list]:
    cleaned = []
    errors = []
    for idx, section in enumerate(sections or []):
        section_id = section.get('id') or f"section-{idx+1}"
        title = (section.get('title') or '').strip()
        content = (section.get('content') or '').strip()
        if not title and not content:
            continue
        if len(title) > 200:
            title = title[:200]
            errors.append(f"Section {section_id} title truncated")
        if len(content) > 15000:
            content = content[:15000]
            errors.append(f"Section {section_id} content truncated")
        cleaned.append({
            'id': section_id,
            'title': title or 'Untitled',
            'content': content,
            'last_modified': section.get('last_modified') or datetime.now().astimezone(tz=None).isoformat(),
        })
        if len(cleaned) >= WIKI_MAX_SECTIONS:
            break
    return cleaned, errors


def _wiki_sections_to_markdown(title: str, sections: Sequence[dict]) -> str:
    parts = [f"# {title.strip() or 'Untitled Wiki'}"]
    for section in sections or []:
        section_title = section.get('title', '').strip() or 'Untitled'
        content = section.get('content', '')
        parts.append(f"\n## {section_title}\n\n{content}")
    return "\n".join(parts).strip() + "\n"


def _generate_wiki_sections(user_id: str, entity_id: Optional[str], docs_table):
    documents: list[dict] = []
    if entity_id:
        entity_resp = docs_table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'ENTITY#{entity_id}'})
        entity_item = entity_resp.get('Item') if isinstance(entity_resp, dict) else None
        doc_ids = entity_item.get('doc_ids', []) if entity_item else []
        if doc_ids:
            documents = _fetch_document_metadata(docs_table, user_id, doc_ids)
    if not documents:
        docs_resp = docs_table.query(
            KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('DOC#')
        )
        documents = docs_resp.get('Items', [])
    documents = sorted(documents, key=lambda item: item.get('updated_at') or item.get('created_at') or '', reverse=True)
    analytics = _compute_temporal_analytics(docs_table, user_id, force=False)
    insights = analytics.get('insights', [])
    topics = analytics.get('monthly_topics', [])
    timeline = analytics.get('sentiment_timeline', [])
    now_iso = datetime.now().astimezone(tz=None).isoformat()
    overview_content = []
    for doc in documents[:3]:
        summary = doc.get('summary') or (doc.get('content') or '')[:400]
        filename = doc.get('filename') or doc.get('doc_id')
        overview_content.append(f"- **{filename}**: {summary}")
    if not overview_content:
        overview_content.append("- No linked documents yet. Start by attaching key notes or uploads.")
    sections = [
        {
            'id': 'overview',
            'title': 'Overview',
            'content': "\n".join(overview_content),
            'last_modified': now_iso,
        }
    ]
    if topics:
        latest_topics = topics[-2:] if len(topics) >= 2 else topics
        topic_lines = []
        for month in latest_topics:
            month_name = month.get('month', 'Recent')
            month_topics = ", ".join(f"{entry['topic']} ({entry['count']})" for entry in month.get('topics', [])[:5])
            topic_lines.append(f"- **{month_name}**: {month_topics or 'No topics yet'}")
        sections.append({
            'id': 'topics',
            'title': 'Trending Topics',
            'content': "\n".join(topic_lines),
            'last_modified': now_iso,
        })
    if insights:
        sections.append({
            'id': 'insights',
            'title': 'Insights & Next Steps',
            'content': "\n".join(f"- {insight}" for insight in insights),
            'last_modified': now_iso,
        })
    if timeline:
        sentiment_lines = []
        recent = timeline[-7:]
        for point in recent:
            sentiment_lines.append(f"- {point['date']}: sentiment {point['sentiment']:+.2f}, emotion {point['emotion']}, {point['words']} words")
        sections.append({
            'id': 'timeline',
            'title': 'Recent Sentiment Timeline',
            'content': "\n".join(sentiment_lines) or 'No recent entries.',
            'last_modified': now_iso,
        })
    return sections[:WIKI_MAX_SECTIONS]


def _save_wiki_page(table, user_id: str, page_id: str, title: str, entity_id: Optional[str], sections: list, version: Optional[int]):
    existing = _get_wiki_page(table, user_id, page_id)
    if existing:
        existing_version = existing.get('version', 1)
        if version is None or version != existing_version:
            raise ValueError("version_conflict")
        new_version = existing_version + 1
        created_at = existing.get('created_at')
    else:
        new_version = 1
        created_at = datetime.now().astimezone(tz=None).isoformat()
    updated_at = datetime.now().astimezone(tz=None).isoformat()
    item = {
        'pk': f'USER#{user_id}',
        'sk': f'WIKI#{page_id}',
        'page_id': page_id,
        'title': title or 'Untitled Wiki',
        'entity_id': entity_id,
        'sections': sections,
        'version': new_version,
        'updated_at': updated_at,
        'created_at': created_at,
        'section_count': len(sections),
    }
    table.put_item(Item=item)
    return item

def lambda_handler(event, context):
    """Main Lambda handler"""
    request_headers = event.get('headers', {})
    headers = make_headers(request_headers=request_headers)
    
    try:
        # Parse request
        if 'requestContext' in event and 'http' in event['requestContext']:
            method = event['requestContext']['http']['method']
            path = event.get('rawPath', '')
        else:
            method = event.get('httpMethod', '')
            path = event.get('path', '')
        
        print(f"📍 {method} {path}")
        
        query_params = event.get('queryStringParameters') or {}

        # OPTIONS
        if method == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        # Health check
        if path == '/dev/health' and method == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'environment': 'dev',
                    'langchain': True,
                    'mcp_enabled': True,
                    'timestamp': datetime.now().isoformat()
                })
            }

        if path.startswith('/dev/documents/') and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }

            parts = path.rstrip('/').split('/')
            if len(parts) < 4:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Document not found'})
                }

            doc_id = parts[3]
            docs_table = dynamodb.Table(DOC_TABLE)
            response_item = docs_table.get_item(Key={'pk': f'USER#{user_id}', 'sk': f'DOC#{doc_id}'})
            item = response_item.get('Item') if isinstance(response_item, dict) else None
            if not item:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Document not found'})
                }

            payload = {
                'doc_id': item.get('doc_id') or doc_id,
                'filename': item.get('filename') or item.get('doc_id'),
                'summary': item.get('summary', ''),
                'questions': item.get('questions', []),
                'content': item.get('content', ''),
                'media_type': item.get('media_type'),
                'entities': item.get('entities', []),
                'highlights': item.get('highlights', []),
                'processing_status': item.get('processing_status'),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at'),
            }
            if 'chat_history' in item:
                payload['chat_history'] = item.get('chat_history') or []

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(payload, cls=DecimalEncoder)
            }

        if path == '/dev/knowledge-graph/entities' and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }

            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                entity_resp = docs_table.query(
                    KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('ENTITY#')
                )
                entity_items = entity_resp.get('Items', [])
                entities = format_user_entities(entity_items)
                doc_relationships, doc_touch_counts = compute_doc_relationships(entity_items)
                doc_ids = set()
                for item in entity_items:
                    for doc_id in item.get('doc_ids', []) or []:
                        doc_ids.add(doc_id)
                for rel in doc_relationships:
                    doc_ids.add(rel['source'])
                    doc_ids.add(rel['target'])
                doc_items = _fetch_document_metadata(docs_table, user_id, list(doc_ids)) if doc_ids else []
                doc_metadata = {}
                now = datetime.now().astimezone(tz=None)
                for doc in doc_items:
                    doc_id = doc.get('doc_id')
                    if not doc_id:
                        continue
                    updated_at = doc.get('updated_at') or doc.get('created_at')
                    updated_dt = _parse_datetime(updated_at)
                    recency_score = 0.3
                    if updated_dt:
                        age_days = max(0, (now - updated_dt).total_seconds() / (60 * 60 * 24))
                        recency_score = max(0.0, 1 - min(age_days, 150) / 150)
                    content_source = doc.get('content') or doc.get('summary') or ''
                    sentiment_score, emotion = _estimate_sentiment(content_source)
                    doc_metadata[doc_id] = {
                        'title': doc.get('filename') or doc_id,
                        'summary': doc.get('summary') or '',
                        'created_at': doc.get('created_at'),
                        'updated_at': doc.get('updated_at'),
                        'recency_score': recency_score,
                        'sentiment_score': sentiment_score,
                        'emotion': emotion,
                        'word_count': len(_tokenize(content_source)),
                        'entity_count': doc_touch_counts.get(doc_id, 0),
                    }
                payload = {
                    'user_id': user_id,
                    'entities': entities,
                    'doc_relationships': doc_relationships,
                    'doc_metadata': doc_metadata,
                }
            except Exception as graph_error:  # noqa: BLE001
                print(f"⚠️ Knowledge graph list failed: {graph_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to load knowledge graph'})
                }

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(payload, cls=DecimalEncoder)
            }

        if path.startswith('/dev/knowledge-graph/entities/') and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }

            parts = path.rstrip('/').split('/')
            if len(parts) < 5:
                return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Entity not found'})}
            entity_id = parts[4]

            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                detail = _get_entity_detail_payload(docs_table, user_id, entity_id)
            except Exception as graph_error:  # noqa: BLE001
                print(f"⚠️ Entity detail load failed: {graph_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to load entity detail'})
                }

            if not detail:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Entity not found'})
                }

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(detail, cls=DecimalEncoder)
            }

        if path.startswith('/dev/knowledge-graph/docs/') and method == 'GET':
            parts = path.rstrip('/').split('/')
            if len(parts) < 5:
                return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Document not found'})}
            doc_id = parts[4]

            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                entities = _get_document_entities(docs_table, doc_id)
            except Exception as graph_error:  # noqa: BLE001
                print(f"⚠️ Document entity load failed: {graph_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Failed to load document entities'})
                }

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'doc_id': doc_id, 'entities': entities}, cls=DecimalEncoder)
            }

        if path == '/dev/wiki' and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                pages = _list_wiki_pages(docs_table, user_id)
            except Exception as wiki_error:  # noqa: BLE001
                print(f"⚠️ Wiki list failed: {wiki_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Unable to load wiki pages'})
                }
            response = []
            for page in pages or []:
                response.append({
                    'page_id': page.get('page_id'),
                    'title': page.get('title'),
                    'entity_id': page.get('entity_id'),
                    'updated_at': page.get('updated_at'),
                    'created_at': page.get('created_at'),
                    'version': page.get('version', 1),
                    'section_count': page.get('section_count', len(page.get('sections', []))),
                })
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'pages': response}, cls=DecimalEncoder)
            }

        if path.startswith('/dev/wiki/') and method == 'GET' and not path.endswith('/export'):
            user_id = query_params.get('user_id') or query_params.get('userId')
            entity_id = query_params.get('entity_id') or query_params.get('entityId')
            auto_create = (query_params.get('auto_create') == 'true')
            page_id = path.rstrip('/').split('/')[3]
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            docs_table = dynamodb.Table(DOC_TABLE)
            page_item = _get_wiki_page(docs_table, user_id, page_id)
            if not page_item and auto_create:
                sections = _generate_wiki_sections(user_id, entity_id, docs_table)
                cleaned_sections, _ = _sanitize_sections(sections)
                page_item = _save_wiki_page(docs_table, user_id, page_id, entity_id or page_id.replace('-', ' ').title(), entity_id, cleaned_sections, version=None)
            if not page_item:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Wiki page not found'})
                }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(page_item, cls=DecimalEncoder)
            }

        if path.startswith('/dev/wiki/') and path.endswith('/export') and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            page_id = path.rstrip('/').split('/')[3]
            docs_table = dynamodb.Table(DOC_TABLE)
            page_item = _get_wiki_page(docs_table, user_id, page_id)
            if not page_item:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'error': 'Wiki page not found'})
                }
            markdown = _wiki_sections_to_markdown(page_item.get('title') or 'Untitled Wiki', page_item.get('sections') or [])
            return {
                'statusCode': 200,
                'headers': {**headers, 'Content-Type': 'text/markdown; charset=utf-8'},
                'body': markdown
            }

        if path == '/dev/wiki' and method in ('POST', 'PUT'):
            body = json.loads(event.get('body') or '{}')
            user_id = body.get('user_id') or query_params.get('user_id')
            entity_id = body.get('entity_id')
            page_id = body.get('page_id') or (entity_id or f'wiki-{uuid.uuid4().hex[:8]}')
            title = body.get('title') or (entity_id.replace('-', ' ').title() if entity_id else 'Untitled Wiki')
            auto_generate = body.get('auto_generate') is True
            sections_payload = body.get('sections') or []
            version = body.get('version')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            docs_table = dynamodb.Table(DOC_TABLE)
            if auto_generate:
                sections_payload = _generate_wiki_sections(user_id, entity_id, docs_table)
                version = None
            cleaned_sections, cleaning_errors = _sanitize_sections(sections_payload)
            try:
                page_item = _save_wiki_page(docs_table, user_id, page_id, title, entity_id, cleaned_sections, version)
            except ValueError as version_error:
                if str(version_error) == 'version_conflict':
                    latest = _get_wiki_page(docs_table, user_id, page_id)
                    return {
                        'statusCode': 409,
                        'headers': headers,
                        'body': json.dumps({'error': 'Version conflict', 'page': latest}, cls=DecimalEncoder)
                    }
                raise
            response_body = {'page': page_item}
            if cleaning_errors:
                response_body['warnings'] = cleaning_errors
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_body, cls=DecimalEncoder)
            }

        if path == '/dev/analytics/temporal' and method == 'GET':
            user_id = query_params.get('user_id') or query_params.get('userId')
            force = query_params.get('force') == 'true'
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                analytics = _compute_temporal_analytics(docs_table, user_id, force=force)
            except Exception as analytics_error:  # noqa: BLE001
                print(f"⚠️ Temporal analytics failed: {analytics_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Unable to compute temporal analytics'})
                }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(analytics, cls=DecimalEncoder)
            }

        if path == '/dev/analytics/temporal/rebuild' and method == 'POST':
            body = json.loads(event.get('body') or '{}')
            user_id = body.get('user_id') or query_params.get('user_id')
            if not user_id:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing user_id'})
                }
            docs_table = dynamodb.Table(DOC_TABLE)
            try:
                analytics = _compute_temporal_analytics(docs_table, user_id, force=True)
            except Exception as analytics_error:  # noqa: BLE001
                print(f"⚠️ Temporal analytics rebuild failed: {analytics_error}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': 'Unable to rebuild temporal analytics'})
                }
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'status': 'recomputed', 'analytics': analytics}, cls=DecimalEncoder)
            }

        # Upload endpoint
        if path in ('/dev/upload', '/upload') and method == 'POST':
            body = json.loads(event['body'])
            user_id = body.get('user_id', 'guest_dev')
            filename = body.get('filename')
            content = body.get('content')
            content_base64 = body.get('content_base64')
            media_type = body.get('media_type')

            if not filename:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing filename'})
                }

            if not content and not content_base64:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing content'})
                }

            doc_id = f"doc_{int(datetime.now().timestamp())}"
            print(f"📄 Processing: {filename}")

            extension = os.path.splitext(filename)[1].lower()
            guessed_type, _ = mimetypes.guess_type(filename)
            media_type = media_type or guessed_type or 'application/octet-stream'

            is_text_like = media_type.startswith('text/') or extension in {'.txt', '.md', '.markdown', '.csv'}
            is_pdf = extension == '.pdf' or media_type == 'application/pdf'

            binary_payload: Optional[bytes] = None

            if content_base64:
                try:
                    binary_payload = base64.b64decode(content_base64)
                except Exception:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'Invalid base64 payload'})
                    }

            if binary_payload and not (is_text_like or is_pdf):
                if not MEDIA_BUCKET or not MEDIA_QUEUE_URL:
                    return {
                        'statusCode': 500,
                        'headers': headers,
                        'body': json.dumps({'error': 'Media processing not configured'})
                    }

                s3_key = f"uploads/{user_id}/{doc_id}/{filename}"
                s3.put_object(
                    Bucket=MEDIA_BUCKET,
                    Key=s3_key,
                    Body=binary_payload,
                    ContentType=media_type,
                )
                print(f"☁️  Stored media in S3 at {s3_key}")

                docs_table = dynamodb.Table(DOC_TABLE)
                docs_table.put_item(Item={
                    'pk': f'USER#{user_id}',
                    'sk': f'DOC#{doc_id}',
                    'doc_id': doc_id,
                    'filename': filename,
                    'media_type': media_type,
                    'processing_status': 'processing',
                    'created_at': datetime.now().isoformat()
                })

                job_payload = {
                    'user_id': user_id,
                    'doc_id': doc_id,
                    'bucket': MEDIA_BUCKET,
                    'key': s3_key,
                    'media_type': media_type,
                    'metadata': body.get('metadata') or {},
                    'segments': body.get('segments') or [],
                }
                sqs.send_message(QueueUrl=MEDIA_QUEUE_URL, MessageBody=json.dumps(job_payload))
                print(f"📬 Enqueued media processing job for {doc_id}")

                return {
                    'statusCode': 202,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'Media received and queued for processing',
                        'doc_id': doc_id,
                        'processing_status': 'processing'
                    })
                }

            if binary_payload and (is_text_like or is_pdf):
                if is_pdf:
                    content = extract_pdf_text(binary_payload)
                else:
                    content = binary_payload.decode('utf-8', errors='ignore')

            if is_pdf and not binary_payload:
                content = extract_pdf_text(content)

            if not content:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Unable to process document content'})
                }

            chunks = text_splitter.split_text(content)
            print(f"✂️  Split into {len(chunks)} chunks")

            print("🔧 Preparing Pinecone payload", flush=True)
            try:
                embeddings_list = embeddings.embed_documents(chunks)
            except Exception as embed_error:
                print(f"❌ Embedding error: {embed_error!r}")
                traceback.print_exc()
                raise

            print("📌 Upserting embeddings to Pinecone", flush=True)
            vectors = []
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings_list)):
                vectors.append(
                    {
                        "id": f"{doc_id}-{idx}",
                        "values": vector,
                        "metadata": {
                            "doc_id": doc_id,
                            "doc_name": filename,
                            "chunk": idx,
                            "text": chunk,
                            "user_id": user_id,
                        },
                    }
                )

            try:
                pinecone_upsert(vectors)
            except Exception as pinecone_error:
                print(f"❌ Pinecone upsert error: {pinecone_error!r}")
                traceback.print_exc()
                raise
            print("✅ Vectorized and stored in Pinecone")

            print("🧠 Generating summary", flush=True)
            summary = generate_summary(content, filename)
            print("🧠 Summary generated", flush=True)

            doc_highlights = generate_highlights(content)
            print(f"🖍️ Generated {len(doc_highlights)} highlights", flush=True)

            print("🕸️ Extracting entities for knowledge graph", flush=True)
            doc_entities = []
            try:
                extracted_entities = run_entity_extraction(content, llm)
                entity_payload = entities_to_document_payload(extracted_entities)
                doc_entities = _prepare_doc_entities(entity_payload)
                print(f"🕸️ Identified {len(doc_entities)} entities", flush=True)
            except Exception as entity_error:  # noqa: BLE001
                print(f"⚠️ Entity extraction failed: {entity_error}")
                doc_entities = []

            questions = [
                f"What are the main topics in {filename}?",
                "Can you summarize the key findings?",
                "What are the most important points?"
            ]

            docs_table = dynamodb.Table(DOC_TABLE)
            print("🗄️  Writing document metadata to DynamoDB", flush=True)
            docs_table.put_item(Item={
                'pk': f'USER#{user_id}',
                'sk': f'DOC#{doc_id}',
                'doc_id': doc_id,
                'filename': filename,
                'media_type': media_type,
                'content': content[:50000],
                'summary': summary,
                'questions': questions,
                'highlights': doc_highlights,
                'processing_status': 'ready',
                'created_at': datetime.now().isoformat(),
                'entities': doc_entities,
                'knowledge_graph_state': 'indexed' if doc_entities else 'no_entities',
            })
            print("🗄️  DynamoDB write complete", flush=True)

            try:
                _upsert_knowledge_graph(docs_table, user_id, doc_id, doc_entities)
            except Exception as kg_error:  # noqa: BLE001
                print(f"⚠️ Knowledge graph persistence failed: {kg_error}")

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Document uploaded',
                    'doc_id': doc_id,
                    'artifact': {
                        'summary': summary,
                        'questions': questions,
                        'highlights': doc_highlights,
                    }
                })
            }
        
        # Chat endpoint with LangChain agent
        if path == '/dev/chat' and method == 'POST':
            body = json.loads(event['body'])
            query = body.get('query') or body.get('messages', [{}])[-1].get('content', '')
            doc_id = body.get('doc_id') or body.get('documentId')
            
            if not query:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'No query provided'})
                }
            
            print(f"💬 Query: {query[:100]}")
            
            # Modify pinecone_retrieve to use doc_id if provided
            original_func = tools[0].func
            if doc_id:
                tools[0].func = lambda q, doc_id=doc_id: pinecone_retrieve(q, doc_id)
            
            # Run agent
            try:
                response_text, citations, tool_traces = research_agent(query)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'response': response_text,
                        'citations': citations,
                        'tool_traces': tool_traces
                    })
                }
            except Exception as e:
                print(f"❌ Agent error: {e}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({
                        'response': 'Sorry, I encountered an error processing your request.',
                        'error': str(e)
                    })
                }
            finally:
                tools[0].func = original_func

        if path == '/dev/autocomplete' and method == 'POST':
            try:
                body = json.loads(event.get('body') or '{}')
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid JSON body'})
                }

            context = (body.get('context') or '').strip()
            max_tokens = int(body.get('max_tokens', 30))
            style = (body.get('style') or '').lower().strip()

            if len(context) < 20:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Context too short'})
                }

            max_tokens = max(10, min(max_tokens, 80))

            style_instructions = {
                'hemingway': "Write with short, vivid sentences and concrete imagery, reminiscent of Ernest Hemingway.",
                'academic': "Adopt a formal, academic tone with precise language and clear argumentation.",
                'casual': "Use a relaxed, conversational tone as if speaking with a friend.",
                'storyteller': "Continue with descriptive, narrative prose that builds atmosphere and emotion.",
                'poetic': "Respond with lyrical, poetic language that leans on metaphor and rhythm.",
            }

            system_prompt = (
                "You are DocumentGPT's AI co-writer. Continue the user's draft naturally, matching their tense, "
                "perspective, and voice. Output only the continuation—no preamble, no closing quotes."
            )
            if style in style_instructions:
                system_prompt += f" {style_instructions[style]}"

            context_window = context[-8000:]
            desired_words = max_tokens // 2
            human_prompt = (
                "Draft continuation request:\n"
                "---------------------------\n"
                f"{context_window}\n\n"
                f"Continue in the same format with roughly {desired_words}-{desired_words + 3} words."
            )

            try:
                response = llm.invoke(
                    [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=human_prompt),
                    ],
                    max_tokens=max_tokens,
                )
                completion = (response.content or "").strip().strip('"').strip("'")

                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'completion': completion})
                }
            except Exception as err:
                print(f"❌ Autocomplete error: {err}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({
                        'error': 'Failed to generate completion',
                        'detail': str(err)
                    })
                }

        # Documents endpoint
        if path == '/documents' and method == 'GET':
            user_id = query_params.get('user_id')
            if not user_id:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({'error': 'Missing user_id'})}

            docs_table = dynamodb.Table(DOC_TABLE)
            resp = docs_table.query(
                KeyConditionExpression=Key('pk').eq(f'USER#{user_id}') & Key('sk').begins_with('DOC#')
            )
            
            documents = [{
                'doc_id': item.get('doc_id'),
                'filename': item.get('filename'),
                'summary': item.get('summary', ''),
                'questions': item.get('questions', []),
                'created_at': item.get('created_at'),
                'entities': item.get('entities', []),
                'knowledge_graph_state': item.get('knowledge_graph_state', 'unknown'),
            } for item in resp.get('Items', [])]
            
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'documents': documents}, cls=DecimalEncoder)}
        
        # Usage endpoint
        if path == '/usage' and method == 'GET':
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'plan': 'premium', 'chats_used': 0, 'limit': -1})}
        
        return {'statusCode': 404, 'headers': headers, 'body': json.dumps({'error': 'Not found'})}
    
    except Exception as e:
        print(f"❌ Error: {e!r}")
        traceback.print_exc()
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)})}
