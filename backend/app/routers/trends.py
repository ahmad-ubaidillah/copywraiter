from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trend
from app.schemas import TrendCreate, TrendRead, TrendUpdate

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("/", response_model=list[TrendRead])
async def list_trends(
    keyword: str | None = None,
    source: str | None = None,
    direction: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Any:
    """List trends with optional filters.

    Trends are global (not user-scoped) — sourced from various platforms.
    """
    query = db.query(Trend)

    if keyword is not None:
        query = query.filter(Trend.keyword.ilike(f"%{keyword}%"))
    if source is not None:
        query = query.filter(Trend.source == source)
    if direction is not None:
        query = query.filter(Trend.direction == direction)

    trends = query.order_by(Trend.tracked_at.desc()).offset(skip).limit(limit).all()
    return trends


@router.get("/{trend_id}", response_model=TrendRead)
async def get_trend(trend_id: str, db: Session = Depends(get_db)) -> Any:
    """Get a single trend by ID."""
    trend = db.query(Trend).filter(Trend.id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trend not found")
    return trend


@router.post("/", response_model=TrendRead, status_code=status.HTTP_201_CREATED)
async def create_trend(
    payload: TrendCreate,
    db: Session = Depends(get_db),
) -> Any:
    """Create a new trend entry."""
    trend = Trend(**payload.model_dump())
    db.add(trend)
    db.commit()
    db.refresh(trend)
    return trend


@router.put("/{trend_id}", response_model=TrendRead)
async def update_trend(
    trend_id: str,
    payload: TrendUpdate,
    db: Session = Depends(get_db),
) -> Any:
    """Update an existing trend."""
    trend = db.query(Trend).filter(Trend.id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trend not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(trend, field, value)

    db.commit()
    db.refresh(trend)
    return trend


@router.delete("/{trend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trend(trend_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a trend."""
    trend = db.query(Trend).filter(Trend.id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trend not found")

    db.delete(trend)
    db.commit()
