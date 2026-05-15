from __future__ import annotations

from typing import Any

SUPPORTED_PLATFORMS: dict[str, str] = {
    "linkedin": "LinkedIn",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "threads": "Threads",
    "youtube": "YouTube (Description)",
    "tiktok": "TikTok (Caption)",
}

PLATFORM_PRESETS: dict[str, dict[str, Any]] = {
    "linkedin": {
        "max_chars": 3000,
        "hashtags": True,
        "emoji_policy": "limited",
        "formatting": "plain",
        "tone": "professional yet conversational",
        "structure": "Hook → Body (1-3 paragraphs) → CTA",
        "banned_patterns": ["excessive emojis", "clickbait", "engagement bait questions"],
        "recommended_length": "1500-2000 characters",
    },
    "facebook": {
        "max_chars": 63206,
        "hashtags": True,
        "emoji_policy": "allowed",
        "formatting": "plain",
        "tone": "casual and engaging",
        "structure": "Attention-grabbing opener → Story/value → Engagement prompt",
        "banned_patterns": ["external links in first paragraph", "excessive hashtags"],
        "recommended_length": "400-800 characters",
    },
    "instagram": {
        "max_chars": 2200,
        "hashtags": True,
        "emoji_policy": "allowed",
        "formatting": "plain",
        "tone": "visual, personal, aspirational",
        "structure": "Hook → Story/Context → CTA → Hashtags (5-15)",
        "banned_patterns": ["links in caption (use bio instead)", "more than 30 hashtags"],
        "recommended_length": "138-150 characters for optimal engagement",
    },
    "threads": {
        "max_chars": 500,
        "hashtags": False,
        "emoji_policy": "allowed",
        "formatting": "plain",
        "tone": "concise, witty, conversational",
        "structure": "Single punchy thought or thread series",
        "banned_patterns": ["long-form content", "excessive hashtags"],
        "recommended_length": "200-300 characters",
    },
    "youtube": {
        "max_chars": 5000,
        "hashtags": True,
        "emoji_policy": "allowed",
        "formatting": "rich",
        "tone": "informative, SEO-optimized",
        "structure": "Summary → Timestamps → Links → Hashtags (3-5)",
        "banned_patterns": ["misleading titles", "keyword stuffing"],
        "recommended_length": "200-500 characters for first 2 lines (visible before 'Show more')",
    },
    "tiktok": {
        "max_chars": 4000,
        "hashtags": True,
        "emoji_policy": "allowed",
        "formatting": "plain",
        "tone": "casual, trend-aware, punchy",
        "structure": "Hook → Context → Hashtags (3-5 trending)",
        "banned_patterns": ["long paragraphs", "formal language", "excessive hashtags"],
        "recommended_length": "100-300 characters",
    },
}


def get_preset(platform: str) -> dict[str, Any] | None:
    return PLATFORM_PRESETS.get(platform)


def get_all_presets() -> dict[str, dict[str, Any]]:
    return PLATFORM_PRESETS


def build_platform_instructions(platform: str, custom_rules: str | None = None) -> str:
    preset = get_preset(platform)
    if not preset:
        return f"Unknown platform: {platform}"

    platform_name = SUPPORTED_PLATFORMS.get(platform, platform)
    lines = [
        f"Platform: {platform_name}",
        f"Max characters: {preset['max_chars']}",
        f"Hashtags: {'Allowed' if preset['hashtags'] else 'Do NOT use'}",
        f"Emoji policy: {preset['emoji_policy']}",
        f"Tone: {preset['tone']}",
        f"Structure: {preset['structure']}",
        f"Recommended: {preset['recommended_length']}",
        "",
        "Avoid:",
    ]
    for p in preset["banned_patterns"]:
        lines.append(f"  - {p}")

    if custom_rules:
        lines.extend(["", "Custom Rules:", custom_rules])

    return "\n".join(lines)


def validate_platform(platform: str) -> bool:
    return platform in SUPPORTED_PLATFORMS
