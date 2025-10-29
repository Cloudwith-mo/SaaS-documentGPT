"""Reusable tool implementations for DocumentGPT agents."""

from __future__ import annotations

from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web for supplemental information."""

    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No web results found."

        snippets = [
            f"• {item['title']}: {item['body'][:200]}... (source: {item['href']})"
            for item in results
        ]
        return "WEB RESULTS:\n" + "\n".join(snippets)
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"⚠️ Web search error: {exc}")
        return "Web search unavailable."


__all__ = ["web_search"]
