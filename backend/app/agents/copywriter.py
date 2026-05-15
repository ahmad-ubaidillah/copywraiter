from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import Draft, Trend, User
from app.services.platform_presets import (
    PLATFORM_PRESETS,
    SUPPORTED_PLATFORMS as PLATFORM_KEYS,
    build_platform_instructions,
    get_preset,
)
from config import settings
from services.ai_client import AIClient, AIClientError

logger = logging.getLogger(__name__)

COPYWRITING_FRAMEWORKS = {
    "AIDA": "Attention → Interest → Desire → Action",
    "PAS": "Problem → Agitate → Solution",
    "BAB": "Before → After → Bridge",
    "FAB": "Feature → Advantage → Benefit",
    "THE_4_CS": "Clear → Concise → Credible → Compelling",
}

HOOK_TYPES = [
    "Negative",
    "Statistical",
    "Curiosity",
    "Authority",
    "Question-Based",
]

KNOWLEDGE_BASE_DIR = settings.BASE_DIR.parent / "knowledge_base"


def _load_json(name: str) -> dict[str, Any]:
    path = KNOWLEDGE_BASE_DIR / name
    if not path.exists():
        logger.warning("Knowledge-base file not found: %s", path)
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load %s: %s", path, exc)
        return {}


def _load_brand_voice() -> dict[str, Any]:
    return _load_json("brand_voice.json")


def _load_profile() -> dict[str, Any]:
    return _load_json("profile.json")


def _load_content_calendar() -> dict[str, Any]:
    return _load_json("content_calendar.json")


def _build_system_prompt(platform: str, language: str = "en") -> str:
    preset = get_preset(platform)
    if not preset:
        preset = get_preset("linkedin")

    tone = preset.get("tone", "professional")
    platform_name = PLATFORM_KEYS.get(platform, platform)

    return (
        f"You are an expert copywriter writing for {platform_name}. "
        f"Tone: {tone}. "
        f"Write content optimized for this platform's audience and conventions. "
        f"Output only the content — no explanations, no meta-commentary."
    )


def _build_user_prompt(
    topic: str,
    platform: str = "linkedin",
    framework: str | None = None,
    hook_type: str | None = None,
    article_context: str = "",
    brand_voice: dict[str, Any] | None = None,
    custom_rules: str | None = None,
    language: str = "en",
) -> str:
    preset = get_preset(platform) or get_preset("linkedin")
    max_chars = preset.get("max_chars", 3000)
    hashtags = preset.get("hashtags", True)
    emoji_policy = preset.get("emoji_policy", "limited")
    structure = preset.get("structure", "")
    banned = preset.get("banned_patterns", [])
    recommended = preset.get("recommended_length", "")

    lines: list[str] = [
        f"PLATFORM: {PLATFORM_KEYS.get(platform, platform)}",
        f"TOPIK: {topic}",
        "",
        "=== PLATFORM RULES ===",
        f"- Max characters: {max_chars}",
        f"- Recommended length: {recommended}",
        f"- Hashtags: {'Allowed' if hashtags else 'Do NOT use hashtags'}",
        f"- Emoji policy: {emoji_policy}",
    ]

    if structure:
        lines.append(f"- Structure: {structure}")

    if banned:
        lines.append("- Avoid:")
        lines.extend(f"  - {b}" for b in banned)

    lines.extend([
        "",
        "=== LARANGAN MUTLAK ===",
        "- NO bold, NO garis pemisah (---)",
        "- NO kata marketing: Jelajahi, Tingkatkan, Solusi, Inovatif, Revolusioner",
        "- NO AI-ism: \"literasi digital\", \"ekosistem informasi\"",
    ])

    if not hashtags:
        lines.append("- NO hashtags (#)")

    if emoji_policy == "discouraged":
        lines.append("- NO emoji")
    elif emoji_policy == "limited":
        lines.append("- Emoji: max 2, hanya jika relevan")

    lines.extend([
        "",
        "=== STRUKTUR ===",
        "1. HOOK — baris pertama yang menarik perhatian",
        "2. BODY — konten utama yang engaging",
        "3. CTA — ajakan bertindak yang natural",
    ])

    if framework:
        framework_desc = COPYWRITING_FRAMEWORKS.get(framework)
        if framework_desc:
            lines.extend(["", f"=== FRAMEWORK: {framework} ===", framework_desc])

    if hook_type:
        lines.extend(["", f"=== HOOK TYPE: {hook_type} ==="])

    if brand_voice:
        bv = brand_voice
        lang = bv.get("language", {})
        style = bv.get("post_style", {})

        avoid_list = lang.get("avoid", [])
        if avoid_list:
            lines.extend(["", "=== YANG HARUS DIHINDARI ==="])
            lines.extend(f"- {a}" for a in avoid_list)

        topics_avoid = bv.get("topics_to_avoid", [])
        if topics_avoid:
            lines.extend(["", "=== TOPIK YANG DIHINDARI ==="])
            lines.extend(f"- {t}" for t in topics_avoid)

        if style.get("formatting"):
            lines.extend(["", f"FORMATTING: {style['formatting']}"])
        if style.get("length"):
            lines.extend(["", f"PANJANG: {style['length']}"])

    if custom_rules:
        lines.extend(["", "=== CUSTOM RULES (Markdown Override) ===", custom_rules])

    if article_context:
        lines.extend(["", "=== KONTEKS ARTIKEL ===", article_context])

    lines.extend([
        "",
        "=== OUTPUT ===",
        f"Langsung copy siap publish. Max {max_chars} karakter.",
    ])

    return "\n".join(lines)


def _sanitize_copy(text: str, platform: str = "linkedin") -> str:
    preset = get_preset(platform) or get_preset("linkedin")
    hashtags_allowed = preset.get("hashtags", True)
    emoji_policy = preset.get("emoji_policy", "limited")

    if not hashtags_allowed:
        text = re.sub(r"#\w+", "", text)

    if emoji_policy == "discouraged":
        text = re.sub(
            r"[\U0001F600-\U0001F64F"
            r"\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF"
            r"\U0001F1E0-\U0001F1FF"
            r"\U00002600-\U000026FF"
            r"\U00002700-\U000027BF]",
            "",
            text,
        )

    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_article_context(url: str, max_chars: int = 2000) -> str:
    import httpx

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        logger.warning("Failed to fetch article at %s: %s", url, exc)
        return "(gagal fetch artikel)"

    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[^;]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


class CopywriterAgent:

    def __init__(self, ai_client: AIClient | None = None) -> None:
        self._ai = ai_client or AIClient()

    def generate(
        self,
        topic: str,
        *,
        platform: str = "linkedin",
        framework: str | None = None,
        hook_type: str | None = None,
        custom_rules: str | None = None,
        language: str = "en",
        trend_id: str | None = None,
        user_id: str | None = None,
        db_session: Session | None = None,
    ) -> dict[str, Any]:
        if platform not in PLATFORM_KEYS:
            platform = "linkedin"

        brand_voice = _load_brand_voice()
        article_context = ""

        if trend_id is not None and db_session is not None:
            trend = db_session.query(Trend).filter(Trend.id == trend_id).first()
            if trend:
                if trend.data and trend.data.get("context"):
                    article_context = trend.data["context"]
                elif trend.data and trend.data.get("source_url"):
                    article_context = _fetch_article_context(trend.data["source_url"])
                if trend.keyword:
                    topic = trend.keyword

        system_prompt = _build_system_prompt(platform, language)
        user_prompt = _build_user_prompt(
            topic=topic,
            platform=platform,
            framework=framework,
            hook_type=hook_type,
            article_context=article_context,
            brand_voice=brand_voice,
            custom_rules=custom_rules,
            language=language,
        )

        preset = get_preset(platform) or get_preset("linkedin")
        max_chars = preset.get("max_chars", 3000)
        max_tokens = max(512, min(max_chars // 2, 4096))

        try:
            result = self._ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=max_tokens,
            )
        except AIClientError as exc:
            logger.error("AI generation failed: %s", exc)
            raise

        raw_content = result["content"]
        content = _sanitize_copy(raw_content, platform)

        output: dict[str, Any] = {
            "topic": topic,
            "platform": platform,
            "content": content,
            "chars": len(content),
            "framework": framework,
            "hook_type": hook_type,
            "ai_provider": result["provider"],
            "ai_model": result["model"],
            "usage": result.get("usage"),
            "draft_id": None,
        }

        if db_session is not None:
            draft = Draft(
                user_id=user_id or "00000000-0000-0000-0000-000000000000",
                title=topic[:255] if topic else None,
                content=content,
                plain_text=content,
                source="ai-generated",
                metadata={
                    "platform": platform,
                    "framework": framework,
                    "hook_type": hook_type,
                    "ai_provider": result["provider"],
                    "ai_model": result["model"],
                    "usage": result.get("usage"),
                    "custom_rules_applied": bool(custom_rules),
                },
            )
            db_session.add(draft)
            db_session.flush()
            output["draft_id"] = draft.id

        return output

    def generate_with_frameworks(
        self,
        topic: str,
        *,
        platform: str = "linkedin",
        frameworks: list[str] | None = None,
        custom_rules: str | None = None,
        language: str = "en",
        user_id: str | None = None,
        db_session: Session | None = None,
    ) -> list[dict[str, Any]]:
        if frameworks is None:
            frameworks = list(COPYWRITING_FRAMEWORKS.keys())

        results: list[dict[str, Any]] = []
        for fw in frameworks:
            try:
                result = self.generate(
                    topic,
                    platform=platform,
                    framework=fw,
                    custom_rules=custom_rules,
                    language=language,
                    user_id=user_id,
                    db_session=db_session,
                )
                results.append(result)
            except AIClientError as exc:
                logger.warning("Framework '%s' failed: %s", fw, exc)
        return results


copywriter_agent = CopywriterAgent()
