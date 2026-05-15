from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_style_analyzer():
    from app.agents.style_analyzer import analyze_style

    text = "Hello world! This is a test. Another sentence here? Yes, it is..."
    result = analyze_style(text)
    assert result["avg_sentence_length"] > 0
    assert result["emoji_count"] == 0
    assert "tone_markers" in result
    assert result["tone_markers"]["exclamation_marks"] == 1
    assert result["tone_markers"]["question_marks"] == 1
    assert result["tone_markers"]["ellipsis"] == 1


def test_style_analyzer_empty():
    from app.agents.style_analyzer import analyze_style

    result = analyze_style("")
    assert result["avg_sentence_length"] == 0
    assert result["emoji_count"] == 0


def test_localization():
    from app.services.localization import (
        SUPPORTED_LANGUAGES,
        get_system_prompt,
        get_banned_words,
        build_language_instructions,
        validate_language,
    )

    assert "en" in SUPPORTED_LANGUAGES
    assert "id_casual" in SUPPORTED_LANGUAGES
    assert get_system_prompt("en") != ""
    assert get_system_prompt("id_casual") != ""
    assert len(get_banned_words("en")) > 0
    assert validate_language("en") is True
    assert validate_language("invalid") is False
    instructions = build_language_instructions("en")
    assert "DILARANG" in instructions or "banned" in instructions.lower() or "KATA" in instructions


def test_strategist():
    from app.agents.strategist import strategist_agent

    result = strategist_agent.select_strategy(
        topic="The problem with remote work",
        research_summary="Studies show 70% of workers struggle with remote work isolation",
        language="en",
    )
    assert result["framework"] in ["AIDA", "PAS", "BAB", "FAB", "THE_4_CS"]
    assert result["hook_type"] in ["Negative", "Statistical", "Curiosity", "Authority", "Question-Based"]
    assert "reasoning" in result
    assert "alternatives" in result


def test_strategist_problem_detection():
    from app.agents.strategist import strategist_agent

    result = strategist_agent.select_strategy(
        topic="masalah produktivitas tim",
        research_summary="Karyawan mengalami masalah fokus dan tantangan kerja remote",
        language="id_casual",
    )
    assert result["framework"] == "PAS"


def test_research_engine():
    from app.services.research_engine import ResearchEngine, Crawl4AIProvider

    engine = ResearchEngine()
    assert engine._crawl4ai is not None
    assert isinstance(engine._crawl4ai, Crawl4AIProvider)


def test_notifier():
    from app.services.notifier import NotificationService

    service = NotificationService()
    assert len(service._notifiers) == 0
    service.configure_from_webhooks({})
    assert len(service._notifiers) == 0


def test_agent_log():
    from app.services.agent_logger import AgentLogService

    log = AgentLogService()
    log.add("test", "info", "Test message")
    entries = log.get_recent()
    assert len(entries) == 1
    assert entries[0]["step"] == "test"
    assert entries[0]["message"] == "Test message"


def test_template_exporter():
    from app.services.template_exporter import TemplateExporter

    exporter = TemplateExporter()
    template = exporter.export(
        style_profile={"avg_sentence_length": 15.5, "emoji_density": 0.02},
        brand_voice={"tone": {"casual": True}},
    )
    assert "copywrAIter" in template
    assert "15.5" in template
    assert "Content Template" in template


def test_platform_presets():
    from app.services.platform_presets import (
        SUPPORTED_PLATFORMS,
        PLATFORM_PRESETS,
        get_preset,
        get_all_presets,
        build_platform_instructions,
        validate_platform,
    )

    assert len(SUPPORTED_PLATFORMS) == 6
    assert "linkedin" in SUPPORTED_PLATFORMS
    assert "tiktok" in SUPPORTED_PLATFORMS
    assert len(PLATFORM_PRESETS) == 6

    preset = get_preset("linkedin")
    assert preset is not None
    assert preset["max_chars"] == 3000
    assert preset["hashtags"] is True

    preset = get_preset("threads")
    assert preset is not None
    assert preset["hashtags"] is False
    assert preset["max_chars"] == 500

    assert validate_platform("instagram") is True
    assert validate_platform("myspace") is False

    instructions = build_platform_instructions("tiktok")
    assert "TikTok" in instructions
    assert "4000" in instructions

    custom = build_platform_instructions("linkedin", "No hashtags please")
    assert "No hashtags please" in custom


def test_config_custom_provider():
    from config import settings

    assert settings.AI_DEFAULT_PROVIDER == "openai"
    assert hasattr(settings, "AI_CUSTOM_BASE_URL")
