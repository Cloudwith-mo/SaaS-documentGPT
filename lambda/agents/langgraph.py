"""LangGraph agent construction helpers for DocumentGPT."""

from __future__ import annotations

import json
import operator
from typing import Annotated, Sequence, Callable, List, Optional, TypedDict

from langchain.tools import Tool
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


DEFAULT_RESEARCH_SYSTEM_PROMPT = (
    "You are DocumentGPT, an AI assistant that helps users understand their documents.\n"
    "IMPORTANT RULES:\n"
    "1. ALWAYS use document_search FIRST for any question about the user's documents.\n"
    "2. Only use web_search if document_search returns no results or the user requests up-to-date context.\n"
    "3. Cite sources with [1], [2], etc. when quoting documents. Cite the most relevant passage.\n"
    "4. If you can't find information, say so clearly and suggest next steps.\n"
    "5. Keep answers concise but informative, focusing on evidence from the documents."
)


class AgentState(TypedDict):
    """State container used by LangGraph execution."""

    messages: Annotated[List[BaseMessage], operator.add]


def build_langgraph_agent(
    llm, system_prompt: str, toolset: Sequence[Tool]
) -> Callable[[str, Optional[List[BaseMessage]]], tuple[str, list, list]]:
    """Compile a LangGraph agent and return a callable runner."""

    tools = list(toolset)
    bound_llm = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def call_model(state: AgentState):
        response = bound_llm.invoke(state["messages"])
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")
    compiled_app = workflow.compile()

    def run(query: str, chat_history: Optional[List[BaseMessage]] = None):
        messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
        if chat_history:
            messages.extend(chat_history)
        messages.append(HumanMessage(content=query))

        result_state = compiled_app.invoke({"messages": messages})
        message_history = result_state["messages"]

        ai_messages = [m for m in message_history if isinstance(m, AIMessage)]
        response_text = ai_messages[-1].content if ai_messages else ""

        citations = []
        tool_traces = []
        for message in message_history:
            if isinstance(message, ToolMessage):
                content_str = (
                    message.content
                    if isinstance(message.content, str)
                    else json.dumps(message.content)
                )
                citations.append(
                    {
                        "tool": message.name or "tool",
                        "result": content_str[:200],
                    }
                )
                tool_traces.append(content_str)

        return response_text, citations, tool_traces

    return run


__all__ = ["DEFAULT_RESEARCH_SYSTEM_PROMPT", "build_langgraph_agent"]
