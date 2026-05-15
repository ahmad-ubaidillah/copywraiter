from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ReplizError(Exception):
    pass


class ReplizClient:
    def __init__(self, api_key: str, base_url: str = "https://api.repliz.io") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> dict[str, Any]:
        try:
            resp = httpx.get(
                f"{self._base_url}/v1/status",
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return {"status": "ok", "data": resp.json()}
        except httpx.HTTPError as exc:
            raise ReplizError(f"Repliz connection test failed: {exc}") from exc

    def create_post(
        self,
        content: str,
        scheduled_at: str | None = None,
        platform: str = "linkedin",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "content": content,
            "platform": platform,
        }
        if scheduled_at:
            payload["scheduled_at"] = scheduled_at

        try:
            resp = httpx.post(
                f"{self._base_url}/v1/posts",
                json=payload,
                headers=self._headers(),
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Repliz post creation failed: {exc}") from exc

    def get_post_status(self, post_id: str) -> dict[str, Any]:
        try:
            resp = httpx.get(
                f"{self._base_url}/v1/posts/{post_id}",
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Repliz status check failed: {exc}") from exc


def get_repliz_client(api_key: str, base_url: str | None = None) -> ReplizClient:
    return ReplizClient(api_key, base_url or "https://api.repliz.io")
