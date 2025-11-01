"""
Utilities for extracting and normalising entities to seed the personal knowledge graph.

The helpers in this module are intentionally side-effect free so that they can be
unit-tested without requiring AWS resources or a live LLM. The Lambda handler is
responsible for wiring in the real model and persistence layer.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

ALLOWED_ENTITY_TYPES = {
    "PERSON",
    "ORG",
    "ORGANIZATION",
    "PROJECT",
    "EVENT",
    "LOCATION",
    "PLACE",
    "DATE",
    "WORK",
    "PRODUCT",
}

# Re-map common variants to a compact set of types we use downstream.
CANONICAL_ENTITY_TYPES = {
    "PERSON": "PERSON",
    "ORG": "ORG",
    "ORGANIZATION": "ORG",
    "COMPANY": "ORG",
    "PROJECT": "PROJECT",
    "INITIATIVE": "PROJECT",
    "EVENT": "EVENT",
    "MEETING": "EVENT",
    "LOCATION": "LOCATION",
    "PLACE": "LOCATION",
    "CITY": "LOCATION",
    "COUNTRY": "LOCATION",
    "DATE": "DATE",
    "TIME": "DATE",
    "WORK": "WORK",
    "WORK_OF_ART": "WORK",
    "BOOK": "WORK",
    "PRODUCT": "PRODUCT",
}

_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Entity:
    """Normalised entity representation used across the pipeline."""

    entity_id: str
    name: str
    type: str
    salience: float
    mentions: List[str]


def _slugify(value: str) -> str:
    """
    Generate a lowercase slug suitable for DynamoDB sort keys.
    """

    value = value.lower().strip()
    value = _NON_SLUG_CHARS.sub("-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "entity"


def _normalise_type(raw_type: str | None) -> str | None:
    if not raw_type:
        return None
    lookup = raw_type.strip().upper()
    if lookup not in ALLOWED_ENTITY_TYPES:
        lookup = CANONICAL_ENTITY_TYPES.get(lookup)
    else:
        lookup = lookup

    if not lookup:
        return None

    # Canonicalise to our known subset.
    return CANONICAL_ENTITY_TYPES.get(lookup, lookup)


def _extract_json_block(raw_text: str) -> str | None:
    """
    Attempt to pull out the JSON payload from a language model response.
    """

    if not raw_text:
        return None

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    return raw_text[start : end + 1]


def parse_entity_payload(raw_text: str) -> List[dict]:
    """
    Parse an LLM response into a list of entity dictionaries.

    The model may return explanatory text around the JSON; we defensively strip
    to the outer-most braces before decoding.
    """

    json_block = _extract_json_block(raw_text)
    if not json_block:
        return []

    try:
        parsed = json.loads(json_block)
    except json.JSONDecodeError:
        return []

    entities = parsed.get("entities") or parsed.get("Entities")
    if not isinstance(entities, list):
        return []
    return [entity for entity in entities if isinstance(entity, dict)]


def _normalise_entity(entity: dict) -> Entity | None:
    name = (entity.get("name") or entity.get("label") or "").strip()
    if not name:
        return None

    entity_type = _normalise_type(entity.get("type") or entity.get("category"))
    if not entity_type:
        return None

    try:
        salience = float(entity.get("salience", 0))
    except (TypeError, ValueError):
        salience = 0.0

    salience = max(0.0, min(salience, 1.0))

    mentions_raw = entity.get("mentions") or entity.get("contexts") or []
    mentions: List[str] = []
    if isinstance(mentions_raw, list):
        for mention in mentions_raw:
            if isinstance(mention, str):
                cleaned = mention.strip()
                if cleaned and cleaned not in mentions:
                    mentions.append(cleaned[:200])

    entity_id = f"{entity_type.lower()}-{_slugify(name)}"
    return Entity(entity_id=entity_id[:80], name=name, type=entity_type, salience=salience, mentions=mentions[:5])


def consolidate_entities(entities: Sequence[dict]) -> List[Entity]:
    """
    Merge raw entity dictionaries into unique, normalised Entity objects.
    """

    consolidated: dict[str, Entity] = {}
    for raw in entities:
        normalised = _normalise_entity(raw)
        if not normalised:
            continue

        existing = consolidated.get(normalised.entity_id)
        if not existing:
            consolidated[normalised.entity_id] = normalised
            continue

        # Merge salience (keep the highest) and append new mentions without duplication.
        mentions = existing.mentions[:]
        for mention in normalised.mentions:
            if mention not in mentions:
                mentions.append(mention)
        merged_salience = max(existing.salience, normalised.salience)
        consolidated[normalised.entity_id] = Entity(
            entity_id=existing.entity_id,
            name=existing.name,
            type=existing.type,
            salience=merged_salience,
            mentions=mentions[:5],
        )

    return list(consolidated.values())


ENTITY_EXTRACTION_PROMPT = """Extract the most relevant named entities mentioned in the user's journal entry or document.

Return a JSON object with this shape:
{
  "entities": [
    {
      "name": "Canonical entity name",
      "type": "PERSON | ORG | PROJECT | EVENT | LOCATION | DATE | PRODUCT | WORK",
      "salience": 0.85,
      "mentions": [
        "Short quote (<=200 chars) showing how the entity was referenced",
        "Second mention if relevant"
      ]
    }
  ]
}

Rules:
- Include no more than 12 entities; prioritise the most important ones.
- Use salience between 0 and 1 (1 = very important to the entry).
- Mentions should be short, trimmed of newlines, and unique.
- If no entities are found, respond with {"entities": []}.
- Respond with JSON only; do not include any commentary.
"""


def run_entity_extraction(text: str, llm, *, max_chars: int = 6000) -> List[Entity]:
    """
    Execute the extraction prompt against the supplied language model.
    """

    snippet = (text or "")[:max_chars]
    if not snippet.strip():
        return []

    messages = [
        {"role": "system", "content": ENTITY_EXTRACTION_PROMPT},
        {
            "role": "user",
            "content": f"Document excerpt:\n---\n{snippet}\n---\nReturn JSON as specified.",
        },
    ]

    response = llm.invoke(messages, max_tokens=600)
    raw_text = getattr(response, "content", "")
    raw_entities = parse_entity_payload(raw_text)
    return consolidate_entities(raw_entities)


def entities_to_document_payload(entities: Iterable[Entity]) -> List[dict]:
    """
    Prepare entity data for storing alongside the document metadata.
    """

    payload: List[dict] = []
    for entity in entities:
        payload.append(
            {
                "entity_id": entity.entity_id,
                "name": entity.name,
                "type": entity.type,
                "salience": round(float(entity.salience), 4),
                "mentions": entity.mentions,
            }
        )
    return payload


def _coerce_decimal(value):
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)
    return value


def format_user_entities(items: Sequence[Dict]) -> List[Dict]:
    """
    Produce a user-facing entity list from DynamoDB rows.
    """

    formatted: List[Dict] = []
    for item in items:
        entity_id = item.get("entity_id") or item.get("sk", "").replace("ENTITY#", "")
        if not entity_id:
            continue

        formatted.append(
            {
                "entity_id": entity_id,
                "name": item.get("entity_name", item.get("name")),
                "type": item.get("entity_type"),
                "doc_count": int(_coerce_decimal(item.get("doc_count", 0))),
                "doc_ids": item.get("doc_ids", []),
                "salience": float(_coerce_decimal(item.get("salience", 0.0))),
                "mentions": item.get("mentions", []),
                "updated_at": item.get("updated_at"),
            }
        )

    return sorted(formatted, key=lambda entry: (-entry["doc_count"], entry["name"] or ""))  # type: ignore[arg-type]


def format_document_entities(items: Sequence[Dict]) -> List[Dict]:
    """
    Prepare doc ↔ entity edge list from DynamoDB rows on the DOC# partition.
    """

    formatted: List[Dict] = []
    for item in items:
        entity_id = item.get("entity_id") or item.get("sk", "").replace("ENTITY#", "")
        if not entity_id:
            continue

        formatted.append(
            {
                "entity_id": entity_id,
                "name": item.get("entity_name"),
                "type": item.get("entity_type"),
                "salience": float(_coerce_decimal(item.get("salience", 0.0))),
                "mentions": item.get("mentions", []),
                "updated_at": item.get("updated_at"),
            }
        )
    return sorted(formatted, key=lambda entry: (-entry["salience"], entry["name"] or ""))  # type: ignore[arg-type]


def format_entity_detail(entity_item: Dict, document_items: Sequence[Dict]) -> Dict:
    """
    Build a composite entity detail payload with related documents.
    """

    documents: List[Dict] = []
    for doc in document_items:
        documents.append(
            {
                "doc_id": doc.get("doc_id"),
                "title": doc.get("filename"),
                "summary": doc.get("summary"),
                "questions": doc.get("questions") or [],
                "media_type": doc.get("media_type"),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
                "highlights": doc.get("highlights") or [],
            }
        )

    return {
        "entity": {
            "entity_id": entity_item.get("entity_id"),
            "name": entity_item.get("entity_name"),
            "type": entity_item.get("entity_type"),
            "doc_count": int(_coerce_decimal(entity_item.get("doc_count", len(documents)))),
            "salience": float(_coerce_decimal(entity_item.get("salience", 0.0))),
            "mentions": entity_item.get("mentions", []),
            "updated_at": entity_item.get("updated_at"),
        },
        "documents": documents,
    }


def compute_doc_relationships(entity_items: Sequence[Dict]) -> Tuple[List[Dict], Dict[str, int]]:
    """Build document-to-document relationship summaries from raw entity items."""

    relationship_map: Dict[Tuple[str, str], Dict[str, object]] = {}
    doc_touch_counts: Dict[str, int] = {}

    for item in entity_items:
        doc_ids = item.get("doc_ids") or []
        if not doc_ids:
            continue

        unique_doc_ids = sorted(set(doc_ids))
        if not unique_doc_ids:
            continue

        for doc_id in unique_doc_ids:
            doc_touch_counts[doc_id] = doc_touch_counts.get(doc_id, 0) + 1

        if len(unique_doc_ids) < 2:
            continue

        entity_name = item.get("entity_name") or item.get("name") or item.get("entity_id")
        for source_id, target_id in combinations(unique_doc_ids, 2):
            key = (source_id, target_id)
            entry = relationship_map.setdefault(
                key,
                {
                    "source": source_id,
                    "target": target_id,
                    "weight": 0,
                    "shared_entities": [],
                },
            )
            entry["weight"] = int(entry.get("weight", 0)) + 1
            if entity_name and entity_name not in entry["shared_entities"]:
                entry["shared_entities"].append(entity_name)

    relationships = sorted(
        relationship_map.values(),
        key=lambda rel: (-int(rel["weight"]), f"{rel['source']}->{rel['target']}")
    )
    return relationships, doc_touch_counts
