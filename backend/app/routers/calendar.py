from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


class ReorderRequest(BaseModel):
    post_id: str
    scheduled_at: str


class SlotRequest(BaseModel):
    date: str
    time: str = "09:00"


@router.get("/")
async def get_calendar(
    user_id: uuid.UUID = Query(...),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None),
    db: Session = Depends(get_db),
) -> Any:
    query = db.query(Post).filter(Post.user_id == user_id)
    if month and year:
        from sqlalchemy import extract
        query = query.filter(
            extract("month", Post.scheduled_at) == month,
            extract("year", Post.scheduled_at) == year,
        )
    posts = query.filter(Post.scheduled_at.isnot(None)).order_by(Post.scheduled_at).all()
    calendar = {}
    for p in posts:
        date_key = p.scheduled_at.strftime("%Y-%m-%d") if p.scheduled_at else "unscheduled"
        if date_key not in calendar:
            calendar[date_key] = []
        calendar[date_key].append({
            "id": str(p.id),
            "title": p.title,
            "content": (p.content or "")[:200],
            "status": p.status,
            "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
            "platform": p.platform,
            "hook_type": p.hook_type,
            "framework": p.framework,
        })
    return {"calendar": calendar}


@router.put("/reorder")
async def reorder_post(
    req: ReorderRequest,
    db: Session = Depends(get_db),
) -> Any:
    post = db.query(Post).filter(Post.id == req.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        post.scheduled_at = datetime.fromisoformat(req.scheduled_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")
    db.commit()
    return {"status": "ok", "scheduled_at": post.scheduled_at.isoformat()}


@router.post("/slot")
async def create_slot(
    req: SlotRequest,
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    scheduled_at = datetime.fromisoformat(f"{req.date}T{req.time}:00")
    post = Post(
        user_id=user_id,
        title="Empty Slot",
        content="",
        status="draft",
        scheduled_at=scheduled_at,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {
        "id": str(post.id),
        "scheduled_at": post.scheduled_at.isoformat(),
        "status": post.status,
    }


@router.delete("/slot/{post_id}", status_code=204)
async def delete_slot(post_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Slot not found")
    db.delete(post)
    db.commit()
