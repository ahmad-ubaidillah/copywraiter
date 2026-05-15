from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LinkedInPost
from app.schemas import LinkedInPostCreate, LinkedInPostRead, LinkedInPostUpdate

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])


@router.get("/posts", response_model=list[LinkedInPostRead])
async def list_linkedin_posts(
    user_id: uuid.UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """List LinkedIn posts for a user."""
    posts = (
        db.query(LinkedInPost)
        .filter(LinkedInPost.user_id == user_id)
        .order_by(LinkedInPost.posted_at.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return posts


@router.get("/posts/{post_id}", response_model=LinkedInPostRead)
async def get_linkedin_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    """Get a single LinkedIn post by ID."""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn post not found")
    return post


@router.post("/posts", response_model=LinkedInPostRead, status_code=status.HTTP_201_CREATED)
async def create_linkedin_post(
    payload: LinkedInPostCreate,
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new LinkedIn post record."""
    post = LinkedInPost(user_id=user_id, **payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/posts/{post_id}", response_model=LinkedInPostRead)
async def update_linkedin_post(
    post_id: uuid.UUID,
    payload: LinkedInPostUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update a LinkedIn post record (e.g. refresh engagement metrics)."""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn post not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_linkedin_post(post_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a LinkedIn post record."""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LinkedIn post not found")

    db.delete(post)
    db.commit()
