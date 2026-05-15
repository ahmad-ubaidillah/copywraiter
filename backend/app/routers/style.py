from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.style_analyzer import analyze_style
from app.database import get_db
from app.models import Setting

router = APIRouter(prefix="/api/style", tags=["Style"])


class AnalyzeRequest(BaseModel):
    text: str


class SaveStyleRequest(BaseModel):
    text: str


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> Any:
    return analyze_style(req.text)


@router.get("/profile")
async def get_profile(
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not found")
    return {"style_profile": setting.style_profile or {}}


@router.put("/profile")
async def update_profile(
    payload: dict[str, Any],
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not found")
    setting.style_profile = payload
    db.commit()
    db.refresh(setting)
    return {"style_profile": setting.style_profile}


@router.post("/save")
async def analyze_and_save(
    req: SaveStyleRequest,
    user_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    profile = analyze_style(req.text)
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        setting = Setting(user_id=user_id, style_profile=profile)
        db.add(setting)
    else:
        setting.style_profile = profile
    db.commit()
    db.refresh(setting)
    return {"style_profile": setting.style_profile}
