from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


class TrendHunterError(Exception):
    pass


class TrendHunter:

    def __init__(self) -> None:
        self._http_client: httpx.Client | None = None

    @property
    def http(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=15.0)
        return self._http_client

    def close(self) -> None:
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def search_google_trends(self, keyword: str) -> dict[str, Any]:
        logger.info("Fetching Google Trends for: %s", keyword)
        try:
            resp = self.http.get(
                "https://trends24.net/api/trends",
                params={"country": "ID", "q": keyword},
                headers={"User-Agent": "copywrAIter/1.0"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "source": "google_trends",
                "keyword": keyword,
                "interest": data.get("interest_over_time", []),
                "volume": data.get("volume", 0),
            }
        except Exception as exc:
            logger.warning("Google Trends fetch failed: %s", exc)
            return {
                "source": "google_trends",
                "keyword": keyword,
                "interest": [],
                "volume": 0,
            }

    def search_twitter_trends(self, keyword: str) -> dict[str, Any]:
        logger.info("Fetching Twitter trends for: %s", keyword)
        try:
            resp = self.http.get(
                "https://getdaytrends.com/api/trends",
                params={"q": keyword},
                headers={"User-Agent": "copywrAIter/1.0"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "source": "twitter",
                "keyword": keyword,
                "tweet_count": data.get("tweet_count", 0),
                "top_hashtags": data.get("hashtags", []),
            }
        except Exception as exc:
            logger.warning("Twitter trends fetch failed: %s", exc)
            return {
                "source": "twitter",
                "keyword": keyword,
                "tweet_count": 0,
                "top_hashtags": [],
            }

    def search_reddit_trends(self, keyword: str) -> dict[str, Any]:
        logger.info("Fetching Reddit trends for: %s", keyword)
        try:
            response = self.http.get(
                "https://www.reddit.com/search.json",
                params={"q": keyword, "limit": 10, "sort": "hot"},
                headers={"User-Agent": "copywrAIter/1.0"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise TrendHunterError(f"Reddit request failed: {exc}") from exc

        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            posts.append({
                "title": post.get("title"),
                "score": post.get("score"),
                "num_comments": post.get("num_comments"),
                "subreddit": post.get("subreddit"),
                "url": post.get("url"),
            })

        return {
            "source": "reddit",
            "keyword": keyword,
            "posts": posts,
        }

    def aggregate(
        self,
        keyword: str,
        sources: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if sources is None:
            sources = ["reddit"]

        source_map = {
            "google_trends": self.search_google_trends,
            "twitter": self.search_twitter_trends,
            "reddit": self.search_reddit_trends,
        }

        results: list[dict[str, Any]] = []
        for src in sources:
            handler = source_map.get(src)
            if handler is None:
                logger.warning("Unknown trend source: %s", src)
                continue
            try:
                result = handler(keyword)
                results.append(result)
            except Exception:
                logger.exception("Trend source '%s' failed for keyword '%s'", src, keyword)
        return results

    def aggregate_with_score(
        self,
        keyword: str,
        sources: list[str] | None = None,
    ) -> dict[str, Any]:
        results = self.aggregate(keyword, sources)
        total_volume = 0
        total_posts = 0
        source_count = len(results)

        for r in results:
            if r.get("volume"):
                total_volume += r["volume"]
            posts = r.get("posts", [])
            total_posts += len(posts)
            for p in posts:
                if p.get("score"):
                    total_volume += p["score"]

        score = (total_volume * 0.4) + (total_posts * 10 * 0.3) + (source_count * 100 * 0.3)

        return {
            "keyword": keyword,
            "sources": results,
            "score": round(score, 2),
            "total_volume": total_volume,
            "total_posts": total_posts,
            "source_count": source_count,
        }


trend_hunter = TrendHunter()
