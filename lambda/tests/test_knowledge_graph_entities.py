import math
from decimal import Decimal
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from knowledge_graph import (  # noqa: E402
    Entity,
    compute_doc_relationships,
    consolidate_entities,
    entities_to_document_payload,
    format_document_entities,
    format_entity_detail,
    format_user_entities,
    parse_entity_payload,
    run_entity_extraction,
)


class StubLLM:
    def __init__(self, content: str):
        self._content = content
        self.calls = []

    def invoke(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})

        class _Response:
            def __init__(self, content: str):
                self.content = content

        return _Response(self._content)


def test_parse_entity_payload_strips_wrapping_text():
    payload = """
    Sure, here you go:
    {
      "entities": [
        {"name": "Ada Lovelace", "type": "Person", "salience": 0.92, "mentions": ["Ada pioneered"]},
        {"name": "Babbage Engine", "type": "Project", "salience": 0.61}
      ]
    }
    Thanks!
    """

    entities = parse_entity_payload(payload)
    assert len(entities) == 2
    assert entities[0]["name"] == "Ada Lovelace"
    assert entities[1]["type"] == "Project"


def test_consolidate_entities_merges_duplicates():
    raw_entities = [
        {"name": "DocumentGPT", "type": "ORG", "salience": 0.6, "mentions": ["DocumentGPT shipped."]},
        {"name": "DocumentGPT", "type": "Organization", "salience": 0.8, "mentions": ["DocumentGPT released"]},
        {"name": "SaaS documentGPT", "type": "ORG", "salience": 0.5},
    ]

    consolidated = consolidate_entities(raw_entities)
    assert len(consolidated) == 2
    docgpt = next(entity for entity in consolidated if entity.name == "DocumentGPT")
    assert math.isclose(docgpt.salience, 0.8)
    assert "DocumentGPT shipped." in docgpt.mentions
    assert "DocumentGPT released" in docgpt.mentions


def test_run_entity_extraction_uses_llm_stub():
    response = '{"entities": [{"name": "Graph DB", "type": "Project", "salience": 0.7, "mentions": ["Graph DB buildout"]}]}'
    llm = StubLLM(response)

    entities = run_entity_extraction("Working on the graph DB buildout", llm)
    assert len(entities) == 1
    assert isinstance(entities[0], Entity)
    assert entities[0].name == "Graph DB"
    assert entities[0].type == "PROJECT"
    assert entities[0].mentions == ["Graph DB buildout"]


@pytest.mark.parametrize(
    "entities",
    [
        [],
        [Entity(entity_id="project-graph-db", name="Graph DB", type="PROJECT", salience=0.75, mentions=["A note"])],
    ],
)
def test_entities_to_document_payload_structure(entities):
    payload = entities_to_document_payload(entities)
    assert isinstance(payload, list)
    for entry in payload:
        assert set(entry.keys()) == {"entity_id", "name", "type", "salience", "mentions"}
        assert isinstance(entry["entity_id"], str)
        assert isinstance(entry["salience"], float)


def test_format_user_entities_sorts_and_coerces_decimal():
    items = [
        {"entity_id": "person-jane", "entity_name": "Jane", "entity_type": "PERSON", "doc_count": Decimal("2"), "salience": Decimal("0.3")},
        {"entity_id": "project-x", "entity_name": "Project X", "entity_type": "PROJECT", "doc_count": Decimal("3.0"), "salience": Decimal("0.4")},
    ]

    formatted = format_user_entities(items)
    assert [entry["entity_id"] for entry in formatted] == ["project-x", "person-jane"]
    assert formatted[0]["doc_count"] == 3
    assert formatted[0]["salience"] == pytest.approx(0.4)


def test_format_document_entities_orders_by_salience():
    items = [
        {"entity_id": "alpha", "entity_name": "Alpha", "entity_type": "PERSON", "salience": Decimal("0.2")},
        {"entity_id": "beta", "entity_name": "Beta", "entity_type": "PROJECT", "salience": Decimal("0.8")},
    ]

    formatted = format_document_entities(items)
    assert [entry["entity_id"] for entry in formatted] == ["beta", "alpha"]
    assert formatted[0]["salience"] == pytest.approx(0.8)


def test_format_entity_detail_combines_documents():
    entity = {
        "entity_id": "project-x",
        "entity_name": "Project X",
        "entity_type": "PROJECT",
        "doc_count": Decimal("2"),
        "mentions": ["Kickoff"],
        "salience": Decimal("0.9"),
        "updated_at": "2025-11-01T00:00:00Z",
    }
    documents = [
        {"doc_id": "doc_alpha", "filename": "Alpha Doc", "summary": "Summary A", "created_at": "2025-10-10T00:00:00Z", "updated_at": "2025-10-11T00:00:00Z", "questions": ["Q1"], "media_type": "text/plain", "highlights": [{"id": "hl-1", "text": "Snippet"}]},
        {"doc_id": "doc_beta", "filename": "Beta Doc", "summary": "Summary B", "created_at": "2025-10-11T00:00:00Z", "updated_at": "2025-10-12T00:00:00Z", "questions": [], "media_type": "text/plain", "highlights": []},
    ]

    detail = format_entity_detail(entity, documents)
    assert detail["entity"]["name"] == "Project X"
    assert detail["entity"]["doc_count"] == 2
    assert len(detail["documents"]) == 2
    first_doc = detail["documents"][0]
    assert first_doc["questions"] == ["Q1"]
    assert first_doc["media_type"] == "text/plain"
    assert first_doc["highlights"] == [{"id": "hl-1", "text": "Snippet"}]
    assert first_doc["updated_at"] == "2025-10-11T00:00:00Z"


def test_compute_doc_relationships_accumulates_shared_entities():
    entity_items = [
        {
            "entity_id": "project-alpha",
            "entity_name": "Project Alpha",
            "doc_ids": ["doc-1", "doc-2", "doc-3"],
        },
        {
            "entity_id": "project-beta",
            "entity_name": "Project Beta",
            "doc_ids": ["doc-2", "doc-3"],
        },
        {
            "entity_id": "solo",
            "doc_ids": ["doc-4"],
        },
    ]

    relationships, doc_counts = compute_doc_relationships(entity_items)

    assert doc_counts == {"doc-1": 1, "doc-2": 2, "doc-3": 2, "doc-4": 1}
    assert relationships
    pair = next(rel for rel in relationships if rel["source"] == "doc-2" and rel["target"] == "doc-3")
    assert pair["weight"] == 2
    assert set(pair["shared_entities"]) == {"Project Alpha", "Project Beta"}
