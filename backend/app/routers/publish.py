from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Post, Setting
from app.services.repliz_client import ReplizClient, ReplizError

router = APIRouter(prefix="/api/repliz", tags=["Repliz Publishing"])


def _get_repliz_client(user_id: str, db: Session) -> ReplizClient:
    setting = db.query(Setting).filter(Setting.user_id == str(user_id)).first()
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
    user_id: str = Query(...),
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
    user_id: str = Query(...),
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
    post_id: str,
    user_id: str = Query(...),
    account_id: str = Query(..., description="Repliz account _id from /accounts"),
    db: Session = Depends(get_db),
) -> Any:
    post = db.query(Post).filter(Post.id == str(post_id), Post.user_id == str(user_id)).first()
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
        post.extra_data = post.extra_data or {}
        post.extra_data["repliz_response"] = result
        db.commit()
        db.refresh(post)
        return {"status": "ok", "message": "Post published via Repliz", "repliz_id": result.get("scheduleId")}
    except ReplizError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class ThreadsPostRequest(BaseModel):
    topic: str
    language: str = "id"
    account_id: str = "6a069f704492e5f5a8f6c871"
    custom_rules: str | None = None


@router.post("/threads", summary="Generate & publish Threads thread in one shot")
async def generate_and_publish_threads(
    req: ThreadsPostRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Generate long-form Threads content via AI and publish as thread chain via Repliz."""
    from app.agents.copywriter import copywriter_agent

    # Generate AI content with threading support
    try:
        result = await copywriter_agent.generate(
            topic=req.topic,
            platform="threads",
            language=req.language,
            user_id=user_id,
            custom_rules=(
                req.custom_rules
                or (
                    "Gaya: jujur, sarkas, relatable, kayak orang ngomong sama temen. "
                    "Bahasa Indonesia campur sehari-hari (warkop). "
                    "NO hashtag, NO emoji, NO bold, NO kata marketing. "
                    "Tulis panjang lebar — lu mau curhat soal ini, curhat aja. "
                    "Pisah tiap bagian cerita dengan ---THREAD_BREAK---"
                )
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {exc}")

    segments = result.get("segments", [])
    content = result.get("content", "")

    if not segments:
        # Fallback: just use the raw content as one post
        segments = [content.strip()] if content.strip() else []

    if not segments:
        raise HTTPException(status_code=500, detail="AI generated empty content")

    # Build replies for thread chain
    replies = []
    for i, seg in enumerate(segments[1:], 1):
        replies.append({
            "description": seg,
            "status": "pending",
        })

    # Publish via Repliz — first segment is main post, rest are replies
    repliz = _get_repliz_client(user_id, db)
    try:
        pub = repliz.create_post(
            content=segments[0],
            account_id=req.account_id,
            post_type="text",
            replies=replies,
        )
    except ReplizError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "status": "ok",
        "topic": req.topic,
        "total_segments": len(segments),
        "main_post_chars": len(segments[0]),
        "replies_count": len(replies),
        "repliz_schedule_id": pub.get("scheduleId"),
        "segments": segments,
    }
