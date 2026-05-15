from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, Setting
from app.services.repliz_client import ReplizClient, ReplizError

router = APIRouter(prefix="/api/repliz", tags=["Repliz Publishing"])


def _get_repliz_client(user_id: uuid.UUID, db: Session) -> ReplizClient:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not found")
    prefs = setting.ai_preferences or {}
    access_key = prefs.get("repliz_access_key", "")
    secret_key = prefs.get("repliz_secret_key", "")
    base_url = prefs.get("repliz_base_url", "https://api.repliz.com")
    if not access_key or not secret_key:
        raise HTTPException(status_code=400, detail="Repliz credentials not configured")
    return ReplizClient(access_key, secret_key, base_url)


@router.post("/test")
async def test_connection(
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    client = _get_repliz_client(user_id, db)
    try:
        result = client.test_connection()
        return {"status": "ok", "message": "Repliz API connection successful", "data": result}
    except ReplizError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/accounts")
async def list_accounts(
    user_id: uuid.UUID = Query(...),
    platform: str | None = Query(None),
    db: Session = Depends(get_db),
) -> Any:
    client = _get_repliz_client(user_id, db)
    try:
        result = client.get_accounts(platform=platform)
        return result
    except ReplizError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/publish/{post_id}")
async def publish_post(
    post_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    account_id: str = Query(..., description="Repliz account _id from /accounts"),
    db: Session = Depends(get_db),
) -> Any:
    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not post.content:
        raise HTTPException(status_code=400, detail="Post has no content")

    client = _get_repliz_client(user_id, db)
    scheduled_at = post.scheduled_at.isoformat() if post.scheduled_at else None
    try:
        result = client.create_post(
            content=post.content,
            account_id=account_id,
            post_type="text",
            scheduled_at=scheduled_at,
        )
        post.status = "scheduled" if scheduled_at else "published"
        post.published_url = result.get("url", "")
        post.metadata = post.metadata or {}
        post.metadata["repliz_response"] = result
        db.commit()
        db.refresh(post)
        return {"status": "ok", "message": "Post published via Repliz", "repliz_id": result.get("id")}
    except ReplizError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
