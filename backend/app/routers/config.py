from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting
from app.services.repliz_client import ReplizClient, ReplizError
from config import settings
from services.ai_client import AIClient, AIClientError

router = APIRouter(prefix="/api/config", tags=["Configuration"])

HERMES_COMPATIBLE_PROVIDERS: dict[str, dict[str, Any]] = {
    "openai": {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "models": ["gpt-4o", "gpt-4o-mini", "o3", "o4-mini"]},
    "anthropic": {"name": "Anthropic", "base_url": "", "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250528", "claude-haiku-4-20250514"]},
    "openrouter": {"name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4", "google/gemini-2.5-pro"]},
    "nous_portal": {"name": "Nous Portal (Hermes)", "base_url": "https://api.nousresearch.com/v1", "models": ["nous-hermes-3", "hermes-4-70b"]},
    "together": {"name": "Together AI", "base_url": "https://api.together.xyz/v1", "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo", "mistralai/Mixtral-8x22B-Instruct-v0.1"]},
    "groq": {"name": "Groq", "base_url": "https://api.groq.com/openai/v1", "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]},
    "deepseek": {"name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "models": ["deepseek-chat", "deepseek-reasoner"]},
    "fireworks": {"name": "Fireworks AI", "base_url": "https://api.fireworks.ai/inference/v1", "models": ["accounts/fireworks/models/llama-v3p3-70b-instruct"]},
    "mistral": {"name": "Mistral AI", "base_url": "https://api.mistral.ai/v1", "models": ["mistral-large-latest", "mistral-small-latest", "pixtral-large-latest"]},
    "cerebras": {"name": "Cerebras", "base_url": "https://api.cerebras.ai/v1", "models": ["llama3.1-70b", "llama3.1-8b"]},
    "gmi_cloud": {"name": "GMI Cloud", "base_url": "https://api.gmi-serving.com/v1", "models": []},
    "xai_grok": {"name": "xAI (Grok)", "base_url": "https://api.x.ai/v1", "models": ["grok-2-latest"]},
    "gemini": {"name": "Google AI Studio (Gemini)", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "models": ["gemini-2.5-pro", "gemini-2.5-flash"]},
    "novita": {"name": "Novita AI", "base_url": "https://api.novita.ai/v3/openai", "models": []},
    "huggingface": {"name": "Hugging Face Inference", "base_url": "https://api-inference.huggingface.co/models", "models": []},
    "ollama": {"name": "Ollama (Local)", "base_url": "http://localhost:11434/v1", "models": ["llama3", "mistral", "qwen2.5"]},
    "lmstudio": {"name": "LM Studio (Local)", "base_url": "http://localhost:1234/v1", "models": []},
    "localai": {"name": "LocalAI (Self-hosted)", "base_url": "http://localhost:8080/v1", "models": []},
    "azure": {"name": "Azure OpenAI", "base_url": "https://YOUR.openai.azure.com/openai/deployments/YOUR_DEPLOYMENT", "models": ["gpt-4o"]},
    "custom": {"name": "Custom Endpoint", "base_url": "", "models": []},
}


class AIConfigRequest(BaseModel):
    provider: str = "openai"
    base_url: str | None = None
    api_key: str = ""
    model: str = "gpt-4o"


class DistributionConfigRequest(BaseModel):
    repliz_access_key: str = ""
    repliz_secret_key: str = ""
    repliz_base_url: str = ""


class NotificationConfigRequest(BaseModel):
    telegram_url: str | None = None
    telegram_chat_id: str | None = None
    discord_url: str | None = None


@router.get("/ai")
async def get_ai_config(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        return {"provider": settings.AI_DEFAULT_PROVIDER, "model": settings.AI_DEFAULT_MODEL, "api_key_masked": True}
    prefs = setting.ai_preferences or {}
    key = prefs.get("api_key", "")
    masked = "*" * 4 + key[-4:] if len(key) > 4 else "not configured"
    return {
        "provider": prefs.get("provider", settings.AI_DEFAULT_PROVIDER),
        "base_url": prefs.get("base_url", ""),
        "model": prefs.get("model", settings.AI_DEFAULT_MODEL),
        "api_key_masked": masked,
    }


@router.post("/ai")
async def save_ai_config(
    req: AIConfigRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        setting = Setting(user_id=user_id, ai_preferences=req.model_dump())
        db.add(setting)
    else:
        prefs = setting.ai_preferences or {}
        prefs.update(req.model_dump())
        setting.ai_preferences = prefs
    db.commit()
    db.refresh(setting)
    return {"status": "ok", "message": "AI configuration saved"}


@router.post("/ai/models")
async def fetch_models(
    req: AIConfigRequest,
) -> Any:
    try:
        if req.provider in HERMES_COMPATIBLE_PROVIDERS:
            preset = HERMES_COMPATIBLE_PROVIDERS[req.provider]
            base_url = req.base_url or preset["base_url"]
        else:
            base_url = req.base_url

        if req.provider == "openai" and not base_url:
            import openai
            c = openai.AsyncOpenAI(api_key=req.api_key)
            models_resp = await c.models.list()
            return {"models": [m.id for m in models_resp.data if "gpt" in m.id or "o" in m.id][:30]}
        elif req.provider == "anthropic":
            return {"models": HERMES_COMPATIBLE_PROVIDERS["anthropic"]["models"]}
        elif req.provider == "custom" or (req.provider in HERMES_COMPATIBLE_PROVIDERS and base_url):
            import openai
            if not base_url:
                raise HTTPException(status_code=400, detail="base_url required for this provider")
            c = openai.AsyncOpenAI(api_key=req.api_key, base_url=base_url)
            models_resp = await c.models.list()
            return {"models": [m.id for m in models_resp.data][:30]}
        elif req.provider in HERMES_COMPATIBLE_PROVIDERS:
            preset = HERMES_COMPATIBLE_PROVIDERS[req.provider]
            if preset["models"]:
                return {"models": preset["models"]}
            import openai
            c = openai.AsyncOpenAI(api_key=req.api_key, base_url=preset["base_url"])
            models_resp = await c.models.list()
            return {"models": [m.id for m in models_resp.data][:30]}
        else:
            return {"models": []}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch models: {exc}")


@router.post("/ai/test")
async def test_ai_connection(
    req: AIConfigRequest,
) -> Any:
    import time
    start = time.time()
    try:
        client = AIClient()
        result = await client.generate(
            prompt="Reply with OK",
            provider=req.provider,
            model=req.model,
            max_tokens=10,
        )
        elapsed = round(time.time() - start, 2)
        return {
            "status": "ok",
            "message": f"Connection successful ({elapsed}s)",
            "response_time_ms": int(elapsed * 1000),
            "model": result["model"],
        }
    except AIClientError as exc:
        elapsed = round(time.time() - start, 2)
        raise HTTPException(status_code=400, detail=f"Connection failed ({elapsed}s): {exc}")


@router.get("/distribution")
async def get_distribution_config(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        return {"repliz_configured": False}
    prefs = setting.ai_preferences or {}
    has_key = bool(prefs.get("repliz_access_key", ""))
    return {
        "repliz_configured": has_key,
        "repliz_base_url": prefs.get("repliz_base_url", ""),
    }


@router.post("/distribution")
async def save_distribution_config(
    req: DistributionConfigRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        setting = Setting(user_id=user_id, ai_preferences=req.model_dump())
        db.add(setting)
    else:
        prefs = setting.ai_preferences or {}
        prefs.update(req.model_dump())
        setting.ai_preferences = prefs
    db.commit()
    db.refresh(setting)
    return {"status": "ok", "message": "Distribution configuration saved"}


@router.post("/distribution/test")
async def test_distribution(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        raise HTTPException(status_code=400, detail="No distribution config found")
    prefs = setting.ai_preferences or {}
    api_key = prefs.get("repliz_access_key", "")
    secret_key = prefs.get("repliz_secret_key", "")
    base_url = prefs.get("repliz_base_url", "https://api.repliz.com")
    if not api_key or not secret_key:
        raise HTTPException(status_code=400, detail="Repliz credentials not configured")
    client = ReplizClient(api_key, secret_key, base_url)
    try:
        result = client.test_connection()
        return {"status": "ok", "message": "Repliz connection OK", "data": result}
    except ReplizError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/notifications")
async def get_notification_config(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        return {"webhooks": {}}
    return {"webhooks": setting.notification_webhooks or {}}


@router.post("/notifications")
async def save_notification_config(
    req: NotificationConfigRequest,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    webhooks = {}
    if req.telegram_url and req.telegram_chat_id:
        webhooks["telegram"] = {"url": req.telegram_url, "chat_id": req.telegram_chat_id}
    if req.discord_url:
        webhooks["discord"] = {"url": req.discord_url}
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting:
        setting = Setting(user_id=user_id, notification_webhooks=webhooks)
        db.add(setting)
    else:
        setting.notification_webhooks = webhooks
    db.commit()
    db.refresh(setting)
    return {"status": "ok", "message": "Notification configuration saved"}


@router.post("/notifications/test")
async def test_notification(
    user_id: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    setting = db.query(Setting).filter(Setting.user_id == user_id).first()
    if not setting or not setting.notification_webhooks:
        raise HTTPException(status_code=400, detail="No notification webhooks configured")
    return {"status": "ok", "message": "Test notification sent"}


@router.get("/system")
async def get_system_info() -> Any:
    import socket
    try:
        import httpx
        ip = httpx.get("https://api.ipify.org", timeout=5).text
    except Exception:
        ip = socket.gethostname()
    return {
        "port": 8080,
        "public_ip": ip,
        "status": "running",
        "version": "1.5",
    }


@router.get("/ai/providers")
async def list_ai_providers() -> Any:
    return {
        "providers": [
            {"id": k, "name": v["name"], "base_url": v["base_url"], "example_models": v["models"]}
            for k, v in HERMES_COMPATIBLE_PROVIDERS.items()
        ]
    }


@router.get("/ai/providers/{provider_id}")
async def get_ai_provider(provider_id: str) -> Any:
    provider = HERMES_COMPATIBLE_PROVIDERS.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")
    return {"id": provider_id, **provider}
