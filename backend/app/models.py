import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, server_default="true")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    settings = relationship("Setting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="user", cascade="all, delete-orphan")
    linkedin_posts = relationship("LinkedInPost", back_populates="user", cascade="all, delete-orphan")
    vault_items = relationship("VaultItem", back_populates="user", cascade="all, delete-orphan")
    niches = relationship("Niche", back_populates="user", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    style_references = relationship("StyleReference", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    bio = Column(Text, nullable=True)
    website = Column(String(512), nullable=True)
    social_links = Column(JSON, nullable=True, default=dict)
    preferences = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="profile")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    theme = Column(String(50), default="light")
    language = Column(String(10), default="en")
    notification_enabled = Column(Boolean, default=True)
    notification_webhooks = Column(JSON, nullable=True, default=dict)
    content_defaults = Column(JSON, nullable=True, default=dict)
    ai_preferences = Column(JSON, nullable=True, default=dict)
    style_profile = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="settings")


class Niche(Base):
    __tablename__ = "niches"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="niches")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=True)
    model = Column(String(100), default="gpt-4")
    temperature = Column(Float, default=0.7)
    config = Column(JSON, nullable=True, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="agents")


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    plain_text = Column(Text, nullable=True)
    niche_id = Column(String(36), ForeignKey("niches.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(50), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True, default=dict)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="drafts")
    niche = relationship("Niche")


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    platform = Column(String(50), nullable=True)
    status = Column(String(50), default="draft")
    hook_type = Column(String(50), nullable=True)
    framework = Column(String(50), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    style_id = Column(String(36), nullable=True)
    published_url = Column(String(512), nullable=True)
    published_at = Column(DateTime, nullable=True)
    niche_id = Column(String(36), ForeignKey("niches.id", ondelete="SET NULL"), nullable=True)
    draft_id = Column(String(36), ForeignKey("drafts.id", ondelete="SET NULL"), nullable=True)
    extra_data = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="posts")
    niche = relationship("Niche")
    draft = relationship("Draft")


class Trend(Base):
    __tablename__ = "trends"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    keyword = Column(String(255), nullable=False, index=True)
    source = Column(String(50), nullable=True)
    direction = Column(String(20), default="stable")
    volume = Column(Float, nullable=True)
    sentiment = Column(Float, nullable=True)
    score = Column(Float, nullable=True, default=0)
    related_keywords = Column(JSON, nullable=True, default=list)
    data = Column(JSON, nullable=True, default=dict)
    tracked_at = Column(DateTime, default=utcnow, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class LinkedInPost(Base):
    __tablename__ = "linkedin_posts"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    linkedin_urn = Column(String(255), nullable=True, unique=True)
    content = Column(Text, nullable=True)
    media_urls = Column(JSON, nullable=True, default=list)
    likes_count = Column(Float, default=0)
    comments_count = Column(Float, default=0)
    shares_count = Column(Float, default=0)
    impressions_count = Column(Float, default=0)
    posted_at = Column(DateTime, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="linkedin_posts")


class Repliz(Base):
    __tablename__ = "repliz"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_post_id = Column(String(36), ForeignKey("linkedin_posts.id", ondelete="SET NULL"), nullable=True)
    original_content = Column(Text, nullable=True)
    generated_reply = Column(Text, nullable=True)
    tone = Column(String(50), default="professional")
    status = Column(String(50), default="draft")
    posted_at = Column(DateTime, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User")
    original_post = relationship("LinkedInPost")


class VaultItem(Base):
    __tablename__ = "vault_items"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    source_url = Column(String(512), nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    category = Column(String(100), nullable=True)
    is_favorite = Column(Boolean, default=False)
    extra_data = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="vault_items")


class StyleReference(Base):
    __tablename__ = "style_references"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reference_text = Column(Text, nullable=True)
    analyzed_profile = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="style_references")
