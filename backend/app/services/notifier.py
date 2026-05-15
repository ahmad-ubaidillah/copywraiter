from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class Notifier(ABC):
    @abstractmethod
    def send(self, event: str, message: str, data: dict[str, Any] | None = None) -> bool:
        pass


class TelegramNotifier(Notifier):
    def __init__(self, url: str, chat_id: str) -> None:
        self._url = url.rstrip("/")
        self._chat_id = chat_id

    def send(self, event: str, message: str, data: dict[str, Any] | None = None) -> bool:
        text = f"[copywrAIter] *{event}*\n{message}"
        try:
            resp = httpx.post(
                f"{self._url}/sendMessage",
                json={"chat_id": self._chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.error("Telegram notification failed: %s", exc)
            return False


class DiscordNotifier(Notifier):
    def __init__(self, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def send(self, event: str, message: str, data: dict[str, Any] | None = None) -> bool:
        embed = {
            "title": f"copywrAIter — {event}",
            "description": message,
            "color": 0x00FF00 if "success" in event.lower() else 0xFF0000,
        }
        try:
            resp = httpx.post(
                self._webhook_url,
                json={"embeds": [embed]},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.error("Discord notification failed: %s", exc)
            return False


class NotificationService:
    def __init__(self) -> None:
        self._notifiers: list[Notifier] = []

    def add_notifier(self, notifier: Notifier) -> None:
        self._notifiers.append(notifier)

    def send(self, event: str, message: str, data: dict[str, Any] | None = None) -> None:
        for notifier in self._notifiers:
            notifier.send(event, message, data)

    def configure_from_webhooks(self, webhooks: dict[str, Any]) -> None:
        self._notifiers.clear()
        if "telegram" in webhooks:
            cfg = webhooks["telegram"]
            self._notifiers.append(TelegramNotifier(cfg["url"], cfg["chat_id"]))
        if "discord" in webhooks:
            self._notifiers.append(DiscordNotifier(webhooks["discord"]["url"]))


notification_service = NotificationService()
