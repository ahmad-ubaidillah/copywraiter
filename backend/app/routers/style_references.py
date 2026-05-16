from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import StyleReference
from app.schemas import StyleReferenceCreate, StyleReferenceRead, StyleReferenceUpdate

router = APIRouter(prefix="/style-references", tags=["Style References"])


@router.get("/", response_model=list[StyleReferenceRead])
async def list_style_references(
    user_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    query = (
        db.query(StyleReference)
        .filter(StyleReference.user_id == user_id)
        .order_by(StyleReference.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return query


@router.get("/{ref_id}", response_model=StyleReferenceRead)
async def get_style_reference(ref_id: str, db: Session = Depends(get_db)) -> Any:
    ref = db.query(StyleReference).filter(StyleReference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style reference not found")
    return ref


@router.post("/", response_model=StyleReferenceRead, status_code=status.HTTP_201_CREATED)
async def create_style_reference(
    payload: StyleReferenceCreate,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    ref = StyleReference(user_id=user_id, **payload.model_dump())
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


@router.put("/{ref_id}", response_model=StyleReferenceRead)
async def update_style_reference(
    ref_id: str,
    payload: StyleReferenceUpdate,
    db: Session = Depends(get_db),
) -> Any:
    ref = db.query(StyleReference).filter(StyleReference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style reference not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(ref, field, value)
    db.commit()
    db.refresh(ref)
    return ref


@router.delete("/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style_reference(ref_id: str, db: Session = Depends(get_db)) -> None:
    ref = db.query(StyleReference).filter(StyleReference.id == ref_id).first()
    if not ref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style reference not found")
    db.delete(ref)
    db.commit()
