from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Profile
from app.schemas import ProfileCreate, ProfileRead, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/{user_id}", response_model=ProfileRead)
async def get_profile(user_id: str, db: Session = Depends(get_db)) -> Any:
    """Get profile for a user."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.post("/{user_id}", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    user_id: str,
    payload: ProfileCreate,
    db: Session = Depends(get_db),
) -> Any:
    """Create a profile for a user."""
    existing = db.query(Profile).filter(Profile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")

    profile = Profile(user_id=user_id, **payload.model_dump(exclude_unset=True))
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/{user_id}", response_model=ProfileRead)
async def update_profile(
    user_id: str,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update a user's profile."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(user_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a user's profile."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    db.delete(profile)
    db.commit()
