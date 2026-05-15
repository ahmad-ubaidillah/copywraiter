from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ResearchError(Exception):
    pass


class ResearchResult(dict):
    pass


class ResearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        pass


class TavilyProvider(ResearchProvider):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        try:
            resp = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True,
                    "include_raw_content": True,
                },
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise ResearchError(f"Tavily API error: {exc}") from exc

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "content": item.get("raw_content", "")[:3000],
            })
        return results


class Crawl4AIProvider(ResearchProvider):
    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        try:
            resp = httpx.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10.0,
            )
            resp.raise_for_status()
            html = resp.text
        except httpx.HTTPError as exc:
            raise ResearchError(f"DuckDuckGo search error: {exc}") from exc

        results = []
        pattern = re.compile(
            r'<a[^>]*class="result[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        snippet_pattern = re.compile(
            r'<a[^>]*class="result[^"]*snippet[^"]*"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        for match in pattern.finditer(html)[:max_results]:
            url = match.group(1)
            title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            snippet_match = snippet_pattern.search(html, match.end())
            snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip() if snippet_match else ""
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
                "content": "",
            })

        if results and results[0]["url"]:
            try:
                content_resp = httpx.get(
                    results[0]["url"],
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10.0,
                    follow_redirects=True,
                )
                content_resp.raise_for_status()
                text = re.sub(r"<script[^>]*>.*?</script>", "", content_resp.text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"&[^;]+;", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                results[0]["content"] = text[:3000]
            except Exception:
                pass

        return results


class ResearchEngine:
    def __init__(self, tavily_api_key: str | None = None) -> None:
        self._tavily_key = tavily_api_key
        self._tavily: TavilyProvider | None = None
        self._crawl4ai = Crawl4AIProvider()

    def _get_tavily(self) -> TavilyProvider | None:
        if self._tavily_key and self._tavily is None:
            self._tavily = TavilyProvider(self._tavily_key)
        return self._tavily

    def search(self, query: str, max_results: int = 10) -> list[dict[str, str]]:
        tavily = self._get_tavily()
        if tavily:
            try:
                return tavily.search(query, max_results)
            except ResearchError as exc:
                logger.warning("Tavily failed, falling back to Crawl4AI: %s", exc)
        return self._crawl4ai.search(query, max_results)

    def search_summary(self, query: str, max_chars: int = 3000) -> str:
        results = self.search(query, max_results=5)
        snippets = []
        for r in results:
            text = r.get("content") or r.get("snippet", "")
            if text:
                snippets.append(text)
        combined = "\n\n".join(snippets)
        return combined[:max_chars]


_research_engine: ResearchEngine | None = None


def get_research_engine(tavily_api_key: str | None = None) -> ResearchEngine:
    global _research_engine
    if _research_engine is None:
        _research_engine = ResearchEngine(tavily_api_key)
    return _research_engine
