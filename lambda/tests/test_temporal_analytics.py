import json
import os
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("OPENAI_API_KEY", "test-openai")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone")
os.environ.setdefault("PINECONE_INDEX_HOST", "example-index-host")
os.environ.setdefault("DOC_TABLE", "docgpt-test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

# Stub heavy langchain modules so we can import dev_handler without optional deps.
if "langchain_openai" not in sys.modules:
    mock_langchain_openai = types.ModuleType("langchain_openai")

    class _StubLLM:
        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, *args, **kwargs):
            return types.SimpleNamespace(content="")

        def bind_tools(self, tools):
            return self

    class _StubEmbeddings:
        def __init__(self, *args, **kwargs):
            pass

        def embed_query(self, query):
            return [0.0]

        def embed_documents(self, docs):
            return [[0.0 for _ in range(3)] for _ in docs]

    mock_langchain_openai.ChatOpenAI = _StubLLM
    mock_langchain_openai.OpenAIEmbeddings = _StubEmbeddings
    sys.modules["langchain_openai"] = mock_langchain_openai

if "langchain" not in sys.modules:
    sys.modules["langchain"] = types.ModuleType("langchain")

if "langchain.text_splitter" not in sys.modules:
    mock_splitter_module = types.ModuleType("langchain.text_splitter")

    class _StubSplitter:
        def __init__(self, *args, **kwargs):
            pass

        def split_text(self, text):
            return [text]

    mock_splitter_module.RecursiveCharacterTextSplitter = _StubSplitter
    sys.modules["langchain.text_splitter"] = mock_splitter_module

if "langchain.tools" not in sys.modules:
    mock_tools = types.ModuleType("langchain.tools")

    class _StubTool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    mock_tools.Tool = _StubTool
    sys.modules["langchain.tools"] = mock_tools

if "langchain_core.messages" not in sys.modules:
    mock_messages = types.ModuleType("langchain_core.messages")

    class _StubMessage:
        def __init__(self, content=None, **kwargs):
            self.content = content
            self.kwargs = kwargs

    mock_messages.HumanMessage = _StubMessage
    mock_messages.SystemMessage = _StubMessage
    mock_messages.AIMessage = _StubMessage
    mock_messages.BaseMessage = _StubMessage
    mock_messages.ToolMessage = _StubMessage
    sys.modules["langchain_core.messages"] = mock_messages

if "langgraph.graph" not in sys.modules:
    mock_graph = types.ModuleType("langgraph.graph")

    class _StubStateGraph:
        def __init__(self, *args, **kwargs):
            pass

        def add_node(self, *args, **kwargs):
            return None

        def set_entry_point(self, *args, **kwargs):
            return None

        def add_conditional_edges(self, *args, **kwargs):
            return None

        def add_edge(self, *args, **kwargs):
            return None

        def compile(self):
            class _Compiled:
                def invoke(self, state):
                    return state

            return _Compiled()

    mock_graph.StateGraph = _StubStateGraph
    sys.modules["langgraph.graph"] = mock_graph

if "langgraph.prebuilt" not in sys.modules:
    mock_prebuilt = types.ModuleType("langgraph.prebuilt")

    class _StubToolNode:
        def __init__(self, tools):
            self.tools = tools

    def _stub_tools_condition(*args, **kwargs):
        return None

    mock_prebuilt.ToolNode = _StubToolNode
    mock_prebuilt.tools_condition = _stub_tools_condition
    sys.modules["langgraph.prebuilt"] = mock_prebuilt

if "ddgs" not in sys.modules:
    mock_ddgs = types.ModuleType("ddgs")

    class _StubDDGS:
        def __init__(self, *args, **kwargs):
            pass

        def text(self, *args, **kwargs):
            return []

    mock_ddgs.DDGS = _StubDDGS
    sys.modules["ddgs"] = mock_ddgs

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dev_handler import (  # type: ignore  # noqa: E402
    _compute_temporal_analytics,
    _estimate_sentiment,
    _generate_predictive_insights,
    _moving_average,
)


def test_estimate_sentiment_positive_negative():
    positive_text = "I am feeling incredibly happy, grateful, and optimistic today!"
    negative_text = "I feel overwhelmed, stressed, and worried about the deadline."

    score_pos, emotion_pos = _estimate_sentiment(positive_text)
    score_neg, emotion_neg = _estimate_sentiment(negative_text)

    assert score_pos > 0
    assert emotion_pos in {"joy", "neutral"}
    assert score_neg < 0
    assert emotion_neg in {"fear", "sadness", "neutral"}


def test_moving_average_basic():
    series = [1, 2, 3, 4, 5]
    result = _moving_average(series, window=3)
    assert result == [1.0, 1.5, 2.0, 3.0, 4.0]


def test_generate_predictive_insights_detects_trends():
    sentiment_ma = [0.45, 0.4, 0.35, 0.3, 0.2, 0.1, 0.05, -0.05, -0.15, -0.25]
    velocity = [{"words": 500} for _ in range(14)]
    topics = [{"month": "2025-10", "topics": [{"topic": "Launch", "count": 4}]}]

    insights = _generate_predictive_insights(sentiment_ma, velocity, topics)
    assert any("downward" in insight.lower() for insight in insights)


class StubTable:
    def __init__(self, docs):
        self.docs = docs
        self.items = {}

    def query(self, **kwargs):
        return {"Items": self.docs}

    def get_item(self, Key):
        return {"Item": self.items.get((Key["pk"], Key["sk"]))}

    def put_item(self, Item):
        self.items[(Item["pk"], Item["sk"])] = Item
        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


def _make_doc(day_offset: int, summary: str, entities=None):
    created = (datetime(2025, 10, 1) + timedelta(days=day_offset)).isoformat()
    return {
        "doc_id": f"doc_{day_offset}",
        "summary": summary,
        "content": summary,
        "created_at": created,
        "entities": entities or [],
    }


def test_compute_temporal_analytics_builds_monthly_topics_and_timeline():
    docs = [
        _make_doc(0, "Excited about the new product launch and roadmap planning.", entities=[
            {"name": "Product Launch"}, {"name": "Roadmap"}
        ]),
        _make_doc(1, "Feeling overwhelmed but making progress on documentation."),
        _make_doc(7, "Calm and confident preparing investor update."),
    ]
    table = StubTable(docs)

    analytics = _compute_temporal_analytics(table, "user-123", force=True)

    assert analytics["user_id"] == "user-123"
    assert analytics["monthly_topics"]
    assert analytics["sentiment_timeline"]
    assert analytics["velocity"]["weekly_totals"]
    assert table.items[(f"USER#user-123", "ANALYTICS#TEMPORAL")]["payload"]
    # Ensure payload is valid JSON
    json.loads(table.items[(f"USER#user-123", "ANALYTICS#TEMPORAL")]["payload"])
