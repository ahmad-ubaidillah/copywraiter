from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Niche
from app.schemas import NicheCreate, NicheRead, NicheUpdate

router = APIRouter(prefix="/niches", tags=["Niches"])


@router.get("/", response_model=list[NicheRead])
async def list_niches(
    user_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """List all niches for a user."""
    niches = (
        db.query(Niche)
        .filter(Niche.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return niches


@router.get("/{niche_id}", response_model=NicheRead)
async def get_niche(niche_id: str, db: Session = Depends(get_db)) -> Any:
    """Get a single niche by ID."""
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Niche not found")
    return niche


@router.post("/", response_model=NicheRead, status_code=status.HTTP_201_CREATED)
async def create_niche(
    payload: NicheCreate,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new niche."""
    niche = Niche(user_id=user_id, **payload.model_dump())
    db.add(niche)
    db.commit()
    db.refresh(niche)
    return niche


@router.put("/{niche_id}", response_model=NicheRead)
async def update_niche(
    niche_id: str,
    payload: NicheUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update a niche."""
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Niche not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(niche, field, value)

    db.commit()
    db.refresh(niche)
    return niche


@router.delete("/{niche_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_niche(niche_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a niche."""
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Niche not found")

    db.delete(niche)
    db.commit()
