from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.services.agent_logger import agent_log

router = APIRouter(prefix="/api/agent-log", tags=["Agent Log"])


@router.get("/")
async def get_agent_log(
    limit: int = Query(100, ge=1, le=1000),
) -> Any:
    return {"log": agent_log.get_recent(limit)}


@router.post("/clear")
async def clear_log() -> Any:
    agent_log.clear()
    return {"status": "ok", "message": "Log cleared"}
