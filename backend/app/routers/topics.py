from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche
from services.trend_hunter import trend_hunter

router = APIRouter(prefix="/api/topics", tags=["Topics"])


class CustomTopicRequest(BaseModel):
    name: str
    description: str | None = None
    keywords: list[str] | None = None


@router.get("/trending")
async def get_trending_topics(
    keyword: str = Query("AI", description="Search keyword for trends"),
) -> Any:
    result = trend_hunter.aggregate_with_score(keyword)
    return {
        "keyword": result["keyword"],
        "score": result["score"],
        "sources": [
            {
                "source": r["source"],
                "posts_count": len(r.get("posts", [])),
                "volume": r.get("volume", 0),
            }
            for r in result["sources"]
        ],
    }


@router.get("/custom")
async def get_custom_topics(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    niches = db.query(Niche).filter(Niche.user_id == user_id, Niche.is_active == True).all()
    return [
        {
            "id": str(n.id),
            "name": n.name,
            "description": n.description,
            "keywords": n.keywords or [],
        }
        for n in niches
    ]


@router.post("/custom", status_code=201)
async def create_custom_topic(
    req: CustomTopicRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    niche = Niche(
        user_id=user_id,
        name=req.name,
        description=req.description,
        keywords=req.keywords or [],
    )
    db.add(niche)
    db.commit()
    db.refresh(niche)
    return {
        "id": str(niche.id),
        "name": niche.name,
        "description": niche.description,
        "keywords": niche.keywords or [],
    }


@router.delete("/custom/{niche_id}", status_code=204)
async def delete_custom_topic(
    niche_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> None:
    niche = db.query(Niche).filter(Niche.id == niche_id, Niche.user_id == user_id).first()
    if not niche:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(niche)
    db.commit()
