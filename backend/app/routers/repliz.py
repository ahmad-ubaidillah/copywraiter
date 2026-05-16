from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Repliz
from app.schemas import ReplizCreate, ReplizRead, ReplizUpdate

router = APIRouter(prefix="/repliz", tags=["Repliz"])


@router.get("/", response_model=list[ReplizRead])
async def list_repliz(
    user_id: str = Query(...),
    status_filter: str | None = Query(None, alias="status"),
    tone: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """List generated replies for a user, with optional filters."""
    query = db.query(Repliz).filter(Repliz.user_id == user_id)

    if status_filter is not None:
        query = query.filter(Repliz.status == status_filter)
    if tone is not None:
        query = query.filter(Repliz.tone == tone)

    replies = query.order_by(Repliz.updated_at.desc()).offset(skip).limit(limit).all()
    return replies


@router.get("/{repliz_id}", response_model=ReplizRead)
async def get_repliz(repliz_id: str, db: Session = Depends(get_db)) -> Any:
    """Get a single generated reply by ID."""
    reply = db.query(Repliz).filter(Repliz.id == repliz_id).first()
    if not reply:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repliz not found")
    return reply


@router.post("/", response_model=ReplizRead, status_code=status.HTTP_201_CREATED)
async def create_repliz(
    payload: ReplizCreate,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new generated reply."""
    reply = Repliz(user_id=user_id, **payload.model_dump())
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


@router.put("/{repliz_id}", response_model=ReplizRead)
async def update_repliz(
    repliz_id: str,
    payload: ReplizUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update a generated reply."""
    reply = db.query(Repliz).filter(Repliz.id == repliz_id).first()
    if not reply:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repliz not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reply, field, value)

    db.commit()
    db.refresh(reply)
    return reply


@router.delete("/{repliz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repliz(repliz_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a generated reply."""
    reply = db.query(Repliz).filter(Repliz.id == repliz_id).first()
    if not reply:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repliz not found")

    db.delete(reply)
    db.commit()
