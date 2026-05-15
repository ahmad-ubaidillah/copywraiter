from __future__ import annotations

import re
from typing import Any

FRAMEWORKS = ["AIDA", "PAS", "BAB", "FAB", "THE_4_CS"]
HOOK_TYPES = ["Negative", "Statistical", "Curiosity", "Authority", "Question-Based"]

PROBLEM_WORDS = re.compile(
    r"(problem|issue|challenge|struggle|pain|frustrat|difficult|masalah|susah|sulit|tantangan)",
    re.IGNORECASE,
)
TRANSFORM_WORDS = re.compile(
    r"(transform|change|become|improve|growth|evolve|before.*after|ubah|menjadi|berubah|tingkatkan)",
    re.IGNORECASE,
)
FEATURE_WORDS = re.compile(
    r"(feature|product|service|tool|platform|app|software|fitur|produk|layanan|aplikasi)",
    re.IGNORECASE,
)
AWARENESS_WORDS = re.compile(
    r"(learn|understand|discover|know|education|aware|guide|tips|belajar|pahami|temukan)",
    re.IGNORECASE,
)
STAT_WORDS = re.compile(r"(\d+%|\d+x|\d+ out of|statistic|data|survey|research|riset|survei)", re.IGNORECASE)
CONTROVERSY_WORDS = re.compile(
    r"(wrong|mistake|myth|lie|stop|don't|beware|danger|salah|mitos|berhenti|jangan|bahaya)",
    re.IGNORECASE,
)
AUTHORITY_WORDS = re.compile(
    r"(expert|leader|top|best|proven|successful|pakar|ahli|terbaik|terbukti|sukses)",
    re.IGNORECASE,
)
QUESTION_WORDS = re.compile(r"(how|what|why|when|who|is it|does|bagaimana|apa|mengapa|apakah)", re.IGNORECASE)


class StrategyAgent:

    def select_strategy(
        self,
        topic: str,
        research_summary: str,
        language: str = "en",
    ) -> dict[str, Any]:
        combined = f"{topic}\n{research_summary}"

        hook = self._pick_hook(combined)
        framework = self._pick_framework(combined)
        reasoning = self._build_reasoning(framework, hook, combined)

        alternatives = self._pick_alternatives(framework, hook)

        return {
            "framework": framework,
            "hook_type": hook,
            "reasoning": reasoning,
            "alternatives": alternatives,
        }

    def _pick_hook(self, text: str) -> str:
        if STAT_WORDS.search(text):
            return "Statistical"
        if CONTROVERSY_WORDS.search(text):
            return "Negative"
        if QUESTION_WORDS.search(text):
            return "Question-Based"
        if AUTHORITY_WORDS.search(text):
            return "Authority"
        return "Curiosity"

    def _pick_framework(self, text: str) -> str:
        if PROBLEM_WORDS.search(text):
            return "PAS"
        if TRANSFORM_WORDS.search(text):
            return "BAB"
        if FEATURE_WORDS.search(text):
            return "FAB"
        if AWARENESS_WORDS.search(text):
            return "AIDA"
        return "THE_4_CS"

    def _build_reasoning(self, framework: str, hook: str, text: str) -> str:
        reasons = []
        if framework == "PAS":
            reasons.append("Topic contains problem indicators — PAS framework addresses pain points directly")
        elif framework == "BAB":
            reasons.append("Topic suggests transformation/change — BAB shows before/after contrast")
        elif framework == "FAB":
            reasons.append("Topic is product/feature-oriented — FAB highlights benefits over features")
        elif framework == "AIDA":
            reasons.append("Topic is educational — AIDA builds awareness to action")
        else:
            reasons.append("General topic — 4Cs ensures clear, concise delivery")

        if hook == "Statistical":
            reasons.append("Research contains data/stats — Statistical hook leverages concrete numbers")
        elif hook == "Negative":
            reasons.append("Controversial/negative angle detected — Negative hook creates urgency")
        elif hook == "Question-Based":
            reasons.append("Question format in topic — Question-Based hook drives curiosity")
        elif hook == "Authority":
            reasons.append("Authority/expert signals found — Authority hook builds credibility")
        else:
            reasons.append("No strong signal — Curiosity hook creates open loop")

        return "; ".join(reasons)

    def _pick_alternatives(self, primary_framework: str, primary_hook: str) -> dict[str, Any]:
        alt_frameworks = [f for f in FRAMEWORKS if f != primary_framework]
        alt_hooks = [h for h in HOOK_TYPES if h != primary_hook]
        return {
            "framework": alt_frameworks[0] if alt_frameworks else "AIDA",
            "hook_type": alt_hooks[0] if alt_hooks else "Curiosity",
        }


strategist_agent = StrategyAgent()
