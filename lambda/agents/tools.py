"""Reusable tool implementations for DocumentGPT agents."""

from __future__ import annotations

from typing import Iterable

from ddgs import DDGS


def _collect_results(generator: Iterable[dict], limit: int) -> list[dict]:
    results = []
    for item in generator:
        results.append(item)
        if len(results) >= limit:
            break
    return results


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web for supplemental information."""

    try:
        with DDGS() as search:
            raw_results = _collect_results(
                search.text(query, max_results=max_results), max_results
            )

        if not raw_results:
            return "No web results found."

        snippets = [
            f"• {item.get('title', 'Untitled')}: "
            f"{(item.get('body') or '')[:200]}... (source: {item.get('href')})"
            for item in raw_results
        ]
        return "WEB RESULTS:\n" + "\n".join(snippets)
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"⚠️ Web search error: {exc}")
        return "Web search unavailable."


__all__ = ["web_search"]
