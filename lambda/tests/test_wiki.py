import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone")
os.environ.setdefault("PINECONE_INDEX_HOST", "test-host")
os.environ.setdefault("DOC_TABLE", "docgpt-test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dev_handler import (  # type: ignore  # noqa: E402
    _generate_wiki_sections,
    _sanitize_sections,
    _save_wiki_page,
    _wiki_sections_to_markdown,
)


class StubTable:
    def __init__(self, docs):
        self.docs = docs
        self.items = {}

    def query(self, **kwargs):
        return {"Items": list(self.docs)}

    def get_item(self, Key):
        return {"Item": self.items.get((Key["pk"], Key["sk"]))}

    def put_item(self, Item):
        self.items[(Item["pk"], Item["sk"])] = Item
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


def _make_doc(doc_id: str, days_ago: int, summary: str):
    created = (datetime(2025, 10, 10) + timedelta(days=days_ago)).isoformat()
    return {
        "pk": f"USER#user-123",
        "sk": f"DOC#{doc_id}",
        "doc_id": doc_id,
        "filename": f"{doc_id}.md",
        "summary": summary,
        "content": summary,
        "created_at": created,
        "updated_at": created,
        "entities": [{"name": "Project Atlas"}],
    }


def test_generate_wiki_sections_includes_topics_and_insights():
    docs = [_make_doc("doc-a", 0, "Completed sprint goals"), _make_doc("doc-b", 1, "Planning next release")]
    table = StubTable(docs)
    sections = _generate_wiki_sections("user-123", None, table)
    assert sections
    titles = {section["title"] for section in sections}
    assert "Overview" in titles
    assert "Trending Topics" in titles or "Insights & Next Steps" in titles


def test_sanitize_sections_limits_and_truncates():
    sections = [{"id": "s1", "title": "A" * 500, "content": "B" * 20000}]
    cleaned, warnings = _sanitize_sections(sections)
    assert cleaned[0]["title"] == "A" * 200
    assert "truncated" in warnings[0].lower()


def test_save_wiki_page_enforces_version_control():
    table = StubTable([])
    sections, _ = _sanitize_sections([{"id": "overview", "title": "Overview", "content": "Intro"}])
    page = _save_wiki_page(table, "user-1", "page-1", "Title", None, sections, version=None)
    assert page["version"] == 1
    updated_sections, _ = _sanitize_sections([{"id": "overview", "title": "Overview", "content": "Updated"}])
    page = _save_wiki_page(table, "user-1", "page-1", "Title", None, updated_sections, version=1)
    assert page["version"] == 2
    try:
        _save_wiki_page(table, "user-1", "page-1", "Title", None, updated_sections, version=1)
    except ValueError as exc:
        assert "version_conflict" in str(exc)
    else:
        raise AssertionError("Expected version conflict")


def test_wiki_markdown_export():
    sections = [
        {"id": "overview", "title": "Overview", "content": "Summary"},
        {"id": "next", "title": "Next Steps", "content": "Plan"},
    ]
    markdown = _wiki_sections_to_markdown("Project Atlas", sections)
    assert "# Project Atlas" in markdown
    assert "## Next Steps" in markdown
