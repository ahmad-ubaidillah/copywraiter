from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting
from app.services.template_exporter import template_exporter

router = APIRouter(prefix="/api/template", tags=["Template"])


@router.get("/preview")
async def preview_template(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    style_profile = setting.style_profile if setting else None
    ai_prefs = setting.ai_preferences if setting else {}
    return {
        "template": template_exporter.export(
            style_profile=style_profile,
            brand_voice=ai_prefs.get("brand_voice"),
        ),
    }


@router.get("/export", response_class=PlainTextResponse)
async def export_template(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> str:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    style_profile = setting.style_profile if setting else None
    ai_prefs = setting.ai_preferences if setting else {}
    return template_exporter.export(
        style_profile=style_profile,
        brand_voice=ai_prefs.get("brand_voice"),
    )
