from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.research_engine import get_research_engine
from services.trend_hunter import trend_hunter

router = APIRouter(prefix="/api/research", tags=["Research"])


class SearchRequest(BaseModel):
    query: str
    max_results: int = 10


class TrendsRequest(BaseModel):
    keyword: str
    sources: list[str] | None = None


@router.post("/search")
async def search(req: SearchRequest) -> Any:
    engine = get_research_engine()
    results = engine.search(req.query, req.max_results)
    return {"query": req.query, "results": results, "count": len(results)}


@router.post("/summary")
async def summary(req: SearchRequest) -> Any:
    engine = get_research_engine()
    text = engine.search_summary(req.query)
    return {"query": req.query, "summary": text, "chars": len(text)}


@router.post("/trends")
async def trends(req: TrendsRequest) -> Any:
    result = trend_hunter.aggregate_with_score(req.keyword, req.sources)
    return result


@router.post("/refresh")
async def refresh() -> Any:
    return {"status": "ok", "message": "Trend refresh triggered"}
