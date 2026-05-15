from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Helpers ──────────────────────────────────────────────────────────────────

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


# ── User ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserRead(TimestampMixin):
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ── Profile ──────────────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    bio: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict[str, Any]] = None
    preferences: Optional[dict[str, Any]] = None


class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    website: Optional[str] = None
    social_links: Optional[dict[str, Any]] = None
    preferences: Optional[dict[str, Any]] = None


class ProfileRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    bio: Optional[str] = None
    website: Optional[str] = None
    social_links: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ── Settings ─────────────────────────────────────────────────────────────────

class SettingCreate(BaseModel):
    theme: Optional[str] = "light"
    language: Optional[str] = "en"
    notification_enabled: Optional[bool] = True
    notification_webhooks: Optional[dict[str, Any]] = None
    content_defaults: Optional[dict[str, Any]] = None
    ai_preferences: Optional[dict[str, Any]] = None
    style_profile: Optional[dict[str, Any]] = None


class SettingUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notification_enabled: Optional[bool] = None
    notification_webhooks: Optional[dict[str, Any]] = None
    content_defaults: Optional[dict[str, Any]] = None
    ai_preferences: Optional[dict[str, Any]] = None
    style_profile: Optional[dict[str, Any]] = None


class SettingRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    theme: str
    language: str
    notification_enabled: bool
    notification_webhooks: dict[str, Any] = Field(default_factory=dict)
    content_defaults: dict[str, Any] = Field(default_factory=dict)
    ai_preferences: dict[str, Any] = Field(default_factory=dict)
    style_profile: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ── Niche ────────────────────────────────────────────────────────────────────

class NicheCreate(BaseModel):
    name: str
    description: Optional[str] = None
    keywords: Optional[list[str]] = None


class NicheUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    is_active: Optional[bool] = None


class NicheRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    is_active: bool

    class Config:
        from_attributes = True


# ── Agent ────────────────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0.7
    config: Optional[dict[str, Any]] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    config: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    model: str
    temperature: float
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool

    class Config:
        from_attributes = True


# ── Draft ────────────────────────────────────────────────────────────────────

class DraftCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    plain_text: Optional[str] = None
    niche_id: Optional[uuid.UUID] = None
    source: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class DraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    plain_text: Optional[str] = None
    niche_id: Optional[uuid.UUID] = None
    source: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    is_archived: Optional[bool] = None


class DraftRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    content: Optional[str] = None
    plain_text: Optional[str] = None
    niche_id: Optional[uuid.UUID] = None
    source: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_archived: bool

    class Config:
        from_attributes = True


# ── Post ─────────────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = "draft"
    hook_type: Optional[str] = None
    framework: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    style_id: Optional[str] = None
    niche_id: Optional[uuid.UUID] = None
    draft_id: Optional[uuid.UUID] = None
    metadata: Optional[dict[str, Any]] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    hook_type: Optional[str] = None
    framework: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    style_id: Optional[str] = None
    published_url: Optional[str] = None
    published_at: Optional[datetime] = None
    niche_id: Optional[uuid.UUID] = None
    draft_id: Optional[uuid.UUID] = None
    metadata: Optional[dict[str, Any]] = None


class PostRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    status: str
    hook_type: Optional[str] = None
    framework: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    style_id: Optional[str] = None
    published_url: Optional[str] = None
    published_at: Optional[datetime] = None
    niche_id: Optional[uuid.UUID] = None
    draft_id: Optional[uuid.UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ── Trend ────────────────────────────────────────────────────────────────────

class TrendCreate(BaseModel):
    keyword: str
    source: Optional[str] = None
    direction: Optional[str] = "stable"
    volume: Optional[float] = None
    sentiment: Optional[float] = None
    score: Optional[float] = 0
    related_keywords: Optional[list[str]] = None
    data: Optional[dict[str, Any]] = None


class TrendUpdate(BaseModel):
    keyword: Optional[str] = None
    source: Optional[str] = None
    direction: Optional[str] = None
    volume: Optional[float] = None
    sentiment: Optional[float] = None
    score: Optional[float] = None
    related_keywords: Optional[list[str]] = None
    data: Optional[dict[str, Any]] = None


class TrendRead(TimestampMixin):
    id: uuid.UUID
    keyword: str
    source: Optional[str] = None
    direction: str
    volume: Optional[float] = None
    sentiment: Optional[float] = None
    score: Optional[float] = 0
    related_keywords: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    tracked_at: datetime

    class Config:
        from_attributes = True


# ── LinkedIn ─────────────────────────────────────────────────────────────────

class LinkedInPostCreate(BaseModel):
    linkedin_urn: Optional[str] = None
    content: Optional[str] = None
    media_urls: Optional[list[str]] = None
    posted_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class LinkedInPostUpdate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[list[str]] = None
    likes_count: Optional[float] = None
    comments_count: Optional[float] = None
    shares_count: Optional[float] = None
    impressions_count: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class LinkedInPostRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    linkedin_urn: Optional[str] = None
    content: Optional[str] = None
    media_urls: list[str] = Field(default_factory=list)
    likes_count: float
    comments_count: float
    shares_count: float
    impressions_count: float
    posted_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ── Repliz ───────────────────────────────────────────────────────────────────

class ReplizCreate(BaseModel):
    original_post_id: Optional[uuid.UUID] = None
    original_content: Optional[str] = None
    generated_reply: Optional[str] = None
    tone: Optional[str] = "professional"
    metadata: Optional[dict[str, Any]] = None


class ReplizUpdate(BaseModel):
    generated_reply: Optional[str] = None
    tone: Optional[str] = None
    status: Optional[str] = None
    posted_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class ReplizRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    original_post_id: Optional[uuid.UUID] = None
    original_content: Optional[str] = None
    generated_reply: Optional[str] = None
    tone: str
    status: str
    posted_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ── VaultItem ────────────────────────────────────────────────────────────────

class VaultItemCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class VaultItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    is_favorite: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class VaultItemRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    content: Optional[str] = None
    source_url: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    is_favorite: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ── StyleReference ───────────────────────────────────────────────────────────

class StyleReferenceCreate(BaseModel):
    reference_text: Optional[str] = None


class StyleReferenceUpdate(BaseModel):
    reference_text: Optional[str] = None
    analyzed_profile: Optional[dict[str, Any]] = None


class StyleReferenceRead(TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    reference_text: Optional[str] = None
    analyzed_profile: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True
