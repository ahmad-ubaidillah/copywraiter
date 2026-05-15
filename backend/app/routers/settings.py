from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting
from app.schemas import SettingCreate, SettingRead, SettingUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/{user_id}", response_model=SettingRead)
async def get_settings(user_id: uuid.UUID, db: Session = Depends(get_db)) -> Any:
    """Get settings for a user."""
    settings = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")
    return settings


@router.post("/{user_id}", response_model=SettingRead, status_code=status.HTTP_201_CREATED)
async def create_settings(
    user_id: uuid.UUID,
    payload: SettingCreate,
    db: Session = Depends(get_db),
) -> Any:
    """Create settings for a user."""
    existing = db.query(Setting).filter(Setting.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Settings already exist")

    settings = Setting(user_id=user_id, **payload.model_dump(exclude_unset=True))
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


@router.put("/{user_id}", response_model=SettingRead)
async def update_settings(
    user_id: uuid.UUID,
    payload: SettingUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update a user's settings."""
    settings = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_settings(user_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a user's settings."""
    settings = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settings not found")

    db.delete(settings)
    db.commit()
