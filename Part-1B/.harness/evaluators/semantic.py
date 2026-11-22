"""Layer 3 - semantic / quality scoring against ground truth and rubric (no LLM judge needed)."""

import re
from datetime import datetime

FIELD_WORDS = {
    "title": ["what", "about"],
    "time": ["time", "when", "what time"],
    "date": ["date", "day", "when"],
    "target_reminder": ["which", "reminder"],
}


def _dt(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _stem(word: str) -> str:
    return word.lower()[:5]


def time_fidelity(output: dict, expected: dict):
    if "remind_at" not in expected:
        return None
    got, want = _dt(output.get("remind_at")), _dt(expected["remind_at"])
    if got is None or want is None or got.tzinfo is None:
        return 0.0
    minutes = abs((got - want).total_seconds()) / 60
    if minutes <= expected.get("tolerance_minutes", 0):
        return 1.0
    return 0.5 if got.astimezone(want.tzinfo).date() == want.date() else 0.0


def title_fidelity(output: dict, expected: dict):
    keywords = expected.get("title_keywords")
    if not keywords:
        return None
    tokens = {_stem(t) for t in re.findall(r"[a-zA-Z']+", output.get("title") or "")}
    hits = sum(1 for k in keywords if _stem(k) in tokens)
    return hits / len(keywords)


def clarification_quality(output: dict, expected: dict):
    if not expected.get("must_clarify"):
        return None
    question = (output.get("clarification_question") or "").lower()
    wanted = expected.get("missing_include_any") or list(FIELD_WORDS)
    return 1.0 if any(w in question for f in wanted for w in FIELD_WORDS.get(f, [])) else 0.0


def score(output: dict, expected: dict) -> dict:
    parts = {
        "time_fidelity": time_fidelity(output, expected),
        "title_fidelity": title_fidelity(output, expected),
        "clarification_quality": clarification_quality(output, expected),
    }
    applicable = [v for v in parts.values() if v is not None]
    return {"components": parts, "score": sum(applicable) / len(applicable) if applicable else 1.0}
