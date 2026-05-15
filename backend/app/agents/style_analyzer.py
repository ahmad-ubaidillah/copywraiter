from __future__ import annotations

import re
from collections import Counter
from typing import Any

STOP_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "that", "this", "these", "those", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her", "they",
    "them", "their", "what", "which", "who", "whom",
})

EMOJI_RE = re.compile(
    r"[\U0001F600-\U0001F64F"
    r"\U0001F300-\U0001F5FF"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF"
    r"\U00002600-\U000026FF"
    r"\U00002700-\U000027BF]"
)

SENTENCE_SPLIT_RE = re.compile(r"[.!?]+|\.{3}")


class StyleAnalyzer:

    def analyze(self, reference_text: str) -> dict[str, Any]:
        if not reference_text or not reference_text.strip():
            return self._empty_profile()

        text = reference_text.strip()
        sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
        words = text.split()
        clean_words = [w.lower().strip(".,!?;:\"'()[]{}") for w in words]
        content_words = [w for w in clean_words if w and w not in STOP_WORDS]

        sentence_lengths = [len(s.split()) for s in sentences]
        avg_sent_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        std_sent_len = 0.0
        if len(sentence_lengths) > 1:
            variance = sum((l - avg_sent_len) ** 2 for l in sentence_lengths) / len(sentence_lengths)
            std_sent_len = variance ** 0.5

        emoji_count = len(EMOJI_RE.findall(text))
        char_count = len(text)
        emoji_density = (emoji_count / char_count * 100) if char_count > 0 else 0

        avg_word_len = sum(len(w) for w in clean_words if w) / len(clean_words) if clean_words else 0
        unique_ratio = len(set(clean_words)) / len(clean_words) if clean_words else 0

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        para_sent_counts = [len([s for s in SENTENCE_SPLIT_RE.split(p) if s.strip()]) for p in paragraphs]
        avg_para_len = sum(para_sent_counts) / len(para_sent_counts) if para_sent_counts else 0

        tone = {
            "exclamation_marks": text.count("!"),
            "question_marks": text.count("?"),
            "ellipsis": text.count("..."),
            "dashes": text.count("—") + text.count("--"),
            "parentheses": text.count("(") + text.count(")"),
        }

        word_freq = Counter(w for w in content_words if len(w) > 2)
        common = [w for w, _ in word_freq.most_common(10)]

        return {
            "avg_sentence_length": round(avg_sent_len, 2),
            "sentence_length_std": round(std_sent_len, 2),
            "emoji_count": emoji_count,
            "emoji_density": round(emoji_density, 4),
            "avg_word_length": round(avg_word_len, 2),
            "unique_word_ratio": round(unique_ratio, 4),
            "tone_markers": tone,
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": round(avg_para_len, 2),
            "common_words": common,
        }

    def _empty_profile(self) -> dict[str, Any]:
        return {
            "avg_sentence_length": 0,
            "sentence_length_std": 0,
            "emoji_count": 0,
            "emoji_density": 0,
            "avg_word_length": 0,
            "unique_word_ratio": 0,
            "tone_markers": {
                "exclamation_marks": 0,
                "question_marks": 0,
                "ellipsis": 0,
                "dashes": 0,
                "parentheses": 0,
            },
            "paragraph_count": 0,
            "avg_paragraph_length": 0,
            "common_words": [],
        }


_style_analyzer = StyleAnalyzer()


def analyze_style(text: str) -> dict[str, Any]:
    return _style_analyzer.analyze(text)
