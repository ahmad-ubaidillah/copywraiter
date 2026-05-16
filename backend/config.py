from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────
    APP_NAME: str = "copywrAIter"
    DEBUG: bool = False
    SECRET_KEY: str = "insecure-dev-key"

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # ── AI Providers ─────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    AI_CUSTOM_BASE_URL: str = ""

    # ── AI Model Defaults ────────────────────────────────────────────
    AI_DEFAULT_PROVIDER: str = "openai"
    AI_DEFAULT_MODEL: str = "gpt-4o"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 4096

    # ── Server ───────────────────────────────────────────────────────
    PORT: int = 8080

    # ── Distribution (Repliz API — Basic Auth) ───────────────────────
    REPLIZ_ACCESS_KEY: str = ""
    REPLIZ_SECRET_KEY: str = ""
    REPLIZ_BASE_URL: str = "https://api.repliz.com"

    # ── Derived / computed ───────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent


settings = Settings()  # singleton
