from __future__ import annotations

from typing import Any

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "id_formal": "Indonesian (Formal)",
    "id_casual": "Indonesian (Casual/Gaul)",
    "custom": "Custom",
}

LANGUAGE_SYSTEM_PROMPTS: dict[str, str] = {
    "en": (
        "You are a professional copywriter writing in English. "
        "Write clear, engaging copy for LinkedIn."
    ),
    "id_formal": (
        "Kamu adalah copywriter profesional yang menulis dalam Bahasa Indonesia formal. "
        "Gunakan bahasa baku, hindari slang, tulis untuk audiens profesional LinkedIn."
    ),
    "id_casual": (
        "Kamu adalah copywriter warga sipil Indonesia. "
        "Nada: jujur, sarkas, capek tapi tetap paham. "
        "Pake bahasa casual/gaul. Tulis buat LinkedIn Indonesia — "
        "target audiens: pekerja kantoran, freelancer, startup people."
    ),
    "custom": "",
}

LANGUAGE_BANNED_WORDS: dict[str, list[str]] = {
    "en": [
        "revolutionary", "game-changing", "cutting-edge",
        "synergy", "leverage", "paradigm shift",
    ],
    "id_formal": [
        "solusi inovatif", "revolusioner", "terdepan",
        "sinergi", "ekosistem digital",
    ],
    "id_casual": [
        "solusi inovatif", "revolusioner", "literasi digital",
        "ekosistem informasi", "jelajahi", "tingkatkan",
    ],
}


def get_system_prompt(language: str) -> str:
    return LANGUAGE_SYSTEM_PROMPTS.get(language, LANGUAGE_SYSTEM_PROMPTS["en"])


def get_banned_words(language: str) -> list[str]:
    return LANGUAGE_BANNED_WORDS.get(language, [])


def build_language_instructions(language: str, custom_rules: str | None = None) -> str:
    lines: list[str] = []
    banned = get_banned_words(language)
    if banned:
        lines.append("=== KATA YANG DILARANG ===")
        lines.extend(f"- {w}" for w in banned)
    if custom_rules:
        lines.append("")
        lines.append("=== ATURAN CUSTOM ===")
        lines.append(custom_rules)
    return "\n".join(lines)


def validate_language(language: str) -> bool:
    return language in SUPPORTED_LANGUAGES
