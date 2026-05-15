from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ReplizError(Exception):
    pass


class ReplizClient:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        base_url: str = "https://api.repliz.com",
    ) -> None:
        self._access_key = access_key
        self._secret_key = secret_key
        self._base_url = base_url.rstrip("/")

    def _auth(self) -> tuple[str, str]:
        return (self._access_key, self._secret_key)

    def _headers(self) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def test_connection(self) -> dict[str, Any]:
        try:
            resp = httpx.get(
                f"{self._base_url}/public/account",
                auth=self._auth(),
                headers=self._headers(),
                params={"page": 1, "limit": 1},
                timeout=10.0,
            )
            resp.raise_for_status()
            return {"status": "ok", "data": resp.json()}
        except httpx.HTTPError as exc:
            raise ReplizError(f"Repliz connection test failed: {exc}") from exc

    def get_accounts(
        self,
        page: int = 1,
        limit: int = 20,
        platform: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "limit": limit}
        if platform:
            params["type"] = platform
        if search:
            params["search"] = search

        try:
            resp = httpx.get(
                f"{self._base_url}/public/account",
                auth=self._auth(),
                headers=self._headers(),
                params=params,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Failed to fetch accounts: {exc}") from exc

    def create_post(
        self,
        content: str,
        account_id: str,
        post_type: str = "text",
        media_url: str | None = None,
        scheduled_at: str | None = None,
        topic: str = "",
        title: str = "",
    ) -> dict[str, Any]:
        medias = []
        if media_url:
            medias.append({
                "alt": "",
                "customThumbnail": False,
                "type": post_type,
                "url": media_url,
            })

        payload: dict[str, Any] = {
            "title": title,
            "description": content,
            "topic": topic,
            "type": post_type,
            "medias": medias,
            "meta": {"title": "", "description": "", "url": ""},
            "additionalInfo": {
                "isAiGenerated": False,
                "isDraft": False,
                "collaborators": [],
                "music": {"id": "", "artist": "", "name": "", "thumbnail": ""},
            },
            "replies": [],
            "accountId": account_id,
        }
        if scheduled_at:
            payload["scheduleAt"] = scheduled_at

        try:
            resp = httpx.post(
                f"{self._base_url}/public/schedule",
                json=payload,
                auth=self._auth(),
                headers=self._headers(),
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Repliz post creation failed: {exc}") from exc

    def get_schedule(self, schedule_id: str) -> dict[str, Any]:
        try:
            resp = httpx.get(
                f"{self._base_url}/public/schedule/{schedule_id}",
                auth=self._auth(),
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Failed to fetch schedule: {exc}") from exc

    def list_schedules(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "limit": limit}
        if status:
            params["status"] = status
        if account_id:
            params["accountIds"] = [account_id]

        try:
            resp = httpx.get(
                f"{self._base_url}/public/schedule",
                auth=self._auth(),
                headers=self._headers(),
                params=params,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Failed to list schedules: {exc}") from exc

    def delete_schedule(self, schedule_id: str) -> None:
        try:
            resp = httpx.delete(
                f"{self._base_url}/public/schedule/{schedule_id}",
                auth=self._auth(),
                headers=self._headers(),
                timeout=10.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ReplizError(f"Failed to delete schedule: {exc}") from exc


def get_repliz_client(
    access_key: str,
    secret_key: str,
    base_url: str | None = None,
) -> ReplizClient:
    return ReplizClient(access_key, secret_key, base_url or "https://api.repliz.com")
