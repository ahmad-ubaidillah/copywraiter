from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.agents.copywriter import CopywriterAgent
from app.agents.strategist import StrategyAgent
from app.services.research_engine import ResearchEngine, get_research_engine

logger = logging.getLogger(__name__)


@dataclass
class WorkflowLogEntry:
    timestamp: str
    step: str
    status: str
    message: str


class ContentWorkflow:

    def __init__(
        self,
        research_engine: ResearchEngine | None = None,
        strategist: StrategyAgent | None = None,
        copywriter: CopywriterAgent | None = None,
        get_session: Any = None,
    ) -> None:
        self._research = research_engine or get_research_engine()
        self._strategist = strategist or StrategyAgent()
        self._copywriter = copywriter or CopywriterAgent()
        self._get_session = get_session
        self._log: list[WorkflowLogEntry] = []

    def run(
        self,
        topic: str,
        language: str = "en",
        user_id: str | None = None,
    ) -> dict[str, Any]:
        self._log.clear()
        self._add_log("workflow", "info", f"Starting workflow for topic: {topic}")

        try:
            research_summary = self._research.search_summary(topic)
            self._add_log("research", "success", f"Research complete: {len(research_summary)} chars")
        except Exception as exc:
            self._add_log("research", "error", str(exc))
            research_summary = ""

        try:
            strategy = self._strategist.select_strategy(topic, research_summary, language)
            self._add_log("strategy", "success", f"Framework: {strategy['framework']}, Hook: {strategy['hook_type']}")
        except Exception as exc:
            self._add_log("strategy", "error", str(exc))
            strategy = {"framework": "THE_4_CS", "hook_type": "Curiosity", "reasoning": "Fallback"}

        try:
            db = self._get_session() if self._get_session else None
            generation = self._copywriter.generate(
                topic,
                platform="linkedin",
                framework=strategy["framework"],
                hook_type=strategy["hook_type"],
                user_id=user_id,
                db_session=db,
            )
            if db:
                db.commit()
                db.close()
            self._add_log("generation", "success", f"Generated {generation['chars']} chars")
        except Exception as exc:
            self._add_log("generation", "error", str(exc))
            generation = {"content": "", "chars": 0, "error": str(exc)}

        self._add_log("workflow", "success", "Workflow complete")

        return {
            "research": {"summary": research_summary, "chars": len(research_summary)},
            "strategy": strategy,
            "generation": generation,
            "status": "success",
        }

    def run_with_variations(
        self,
        topic: str,
        language: str = "en",
        user_id: str | None = None,
    ) -> dict[str, Any]:
        self._log.clear()
        self._add_log("workflow", "info", f"Starting variation workflow for topic: {topic}")

        try:
            research_summary = self._research.search_summary(topic)
            self._add_log("research", "success", f"Research complete: {len(research_summary)} chars")
        except Exception as exc:
            self._add_log("research", "error", str(exc))
            research_summary = ""

        try:
            strategy = self._strategist.select_strategy(topic, research_summary, language)
            self._add_log("strategy", "success", f"Primary: {strategy['framework']}+{strategy['hook_type']}")
        except Exception as exc:
            self._add_log("strategy", "error", str(exc))
            strategy = {
                "framework": "THE_4_CS",
                "hook_type": "Curiosity",
                "reasoning": "Fallback",
                "alternatives": {"framework": "PAS", "hook_type": "Negative"},
            }

        alt = strategy.get("alternatives", {})
        alt_framework = alt.get("framework", "PAS")
        alt_hook = alt.get("hook_type", "Negative")

        variations = []
        db = self._get_session() if self._get_session else None

        for i, (fw, hook, label) in enumerate([
            (strategy["framework"], strategy["hook_type"], "A"),
            (alt_framework, alt_hook, "B"),
        ]):
            try:
                result = self._copywriter.generate(
                    topic,
                    platform="linkedin",
                    framework=fw,
                    hook_type=hook,
                    user_id=user_id,
                    db_session=db,
                )
                result["variation"] = label
                variations.append(result)
                self._add_log("generation", "success", f"Variation {label}: {result['chars']} chars")
            except Exception as exc:
                self._add_log("generation", "error", f"Variation {label} failed: {exc}")
                variations.append({"variation": label, "content": "", "chars": 0, "error": str(exc)})

        if db:
            db.commit()
            db.close()

        self._add_log("workflow", "success", "Variation workflow complete")

        return {
            "research": {"summary": research_summary, "chars": len(research_summary)},
            "strategy": strategy,
            "variations": variations,
            "status": "success",
        }

    def get_log(self) -> list[dict[str, str]]:
        return [
            {
                "timestamp": e.timestamp,
                "step": e.step,
                "status": e.status,
                "message": e.message,
            }
            for e in self._log
        ]

    def _add_log(self, step: str, status: str, message: str) -> None:
        self._log.append(WorkflowLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            step=step,
            status=status,
            message=message,
        ))


_content_workflow: ContentWorkflow | None = None


def get_content_workflow(get_session: Any = None) -> ContentWorkflow:
    global _content_workflow
    if _content_workflow is None:
        _content_workflow = ContentWorkflow(get_session=get_session)
    return _content_workflow
