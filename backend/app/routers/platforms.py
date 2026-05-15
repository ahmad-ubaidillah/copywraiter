from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting
from app.services.platform_presets import (
    SUPPORTED_PLATFORMS,
    build_platform_instructions,
    get_all_presets,
    get_preset,
    validate_platform,
)

router = APIRouter(prefix="/api/platforms", tags=["Platforms"])


@router.get("/")
async def list_platforms() -> Any:
    return {
        "platforms": [
            {"id": k, "name": v, **get_preset(k)}
            for k, v in SUPPORTED_PLATFORMS.items()
        ]
    }


@router.get("/{platform}")
async def get_platform(platform: str) -> Any:
    preset = get_preset(platform)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not found")
    return {"id": platform, "name": SUPPORTED_PLATFORMS.get(platform, platform), **preset}


@router.get("/{platform}/instructions")
async def get_platform_instructions(
    platform: str,
    custom_rules: str | None = Query(None),
) -> Any:
    if not validate_platform(platform):
        raise HTTPException(status_code=404, detail=f"Platform '{platform}' not found")
    return {"instructions": build_platform_instructions(platform, custom_rules)}


@router.get("/config")
async def get_platform_config(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        return {"platform_configs": {}}
    prefs = setting.ai_preferences or {}
    return {"platform_configs": prefs.get("platform_configs", {})}


class PlatformConfigRequest(BaseModel):
    platform: str
    max_chars: int | None = None
    tone: str | None = None
    custom_rules: str | None = None


@router.post("/config")
async def save_platform_config(
    req: PlatformConfigRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    if not validate_platform(req.platform):
        raise HTTPException(status_code=400, detail=f"Unknown platform: {req.platform}")

    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        setting = Setting(user_id=user_id)
        db.add(setting)

    prefs = setting.ai_preferences or {}
    configs = prefs.get("platform_configs", {})

    preset = get_preset(req.platform) or {}
    config = {
        "max_chars": req.max_chars or preset.get("max_chars"),
        "tone": req.tone or preset.get("tone", ""),
        "custom_rules": req.custom_rules or "",
    }
    configs[req.platform] = config
    prefs["platform_configs"] = configs
    setting.ai_preferences = prefs

    db.commit()
    db.refresh(setting)
    return {"status": "ok", "platform_configs": configs}
