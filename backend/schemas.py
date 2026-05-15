from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Project ────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    brand_name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    tone: str | None = "professional"
    target_audience: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    brand_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    tone: str | None = None
    target_audience: str | None = None


class ProjectRead(BaseModel):
    id: uuid.UUID
    name: str
    brand_name: str
    description: str | None
    tone: str | None
    target_audience: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Copy ────────────────────────────────────────────────────────────────────

class CopyCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    platform: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    prompt_used: str | None = None


class CopyUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    platform: str | None = None
    status: str | None = Field(None, pattern=r"^(draft|reviewed|approved)$")


class CopyRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    content: str
    platform: str | None
    status: str
    ai_provider: str | None
    ai_model: str | None
    prompt_used: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Trend ───────────────────────────────────────────────────────────────────

class TrendCreate(BaseModel):
    project_id: uuid.UUID
    keyword: str = Field(..., min_length=1, max_length=255)
    source: str | None = None
    summary: str | None = None
    score: float | None = Field(None, ge=0, le=100)
    raw_data: dict[str, Any] | None = None


class TrendRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    keyword: str
    source: str | None
    summary: str | None
    score: float | None
    raw_data: dict[str, Any] | None
    collected_at: datetime

    model_config = {"from_attributes": True}


# ── AI Generation ───────────────────────────────────────────────────────────

class AIGenerateRequest(BaseModel):
    project_id: uuid.UUID
    prompt: str = Field(..., min_length=1)
    platform: str | None = None
    tone: str | None = None
    provider: str | None = None
    model: str | None = None


class AIGenerateResponse(BaseModel):
    content: str
    provider: str
    model: str
    usage: dict[str, int] | None = None
