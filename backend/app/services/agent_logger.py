from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

MAX_ENTRIES = 1000


class AgentLogService:
    def __init__(self) -> None:
        self._entries: deque[dict[str, Any]] = deque(maxlen=MAX_ENTRIES)
        self._lock = threading.Lock()

    def add(self, step: str, status: str, message: str, data: dict[str, Any] | None = None) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "status": status,
            "message": message,
            "data": data or {},
        }
        with self._lock:
            self._entries.append(entry)

    def get_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


agent_log = AgentLogService()
