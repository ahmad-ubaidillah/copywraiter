from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Draft
from app.schemas import DraftCreate, DraftRead, DraftUpdate

router = APIRouter(prefix="/drafts", tags=["Drafts"])


@router.get("/", response_model=list[DraftRead])
async def list_drafts(
    user_id: uuid.UUID = Query(...),
    is_archived: bool | None = None,
    source: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """List drafts for a user, with optional filters."""
    query = db.query(Draft).filter(Draft.user_id == user_id)

    if is_archived is not None:
        query = query.filter(Draft.is_archived == is_archived)
    if source is not None:
        query = query.filter(Draft.source == source)

    drafts = query.order_by(Draft.updated_at.desc()).offset(skip).limit(limit).all()
    return drafts


@router.get("/{draft_id}", response_model=DraftRead)
async def get_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    """Get a single draft by ID."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return draft


@router.post("/", response_model=DraftRead, status_code=status.HTTP_201_CREATED)
async def create_draft(
    payload: DraftCreate,
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new draft."""
    draft = Draft(user_id=user_id, **payload.model_dump())
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.put("/{draft_id}", response_model=DraftRead)
async def update_draft(
    draft_id: uuid.UUID,
    payload: DraftUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing draft."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)

    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a draft."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    db.delete(draft)
    db.commit()
