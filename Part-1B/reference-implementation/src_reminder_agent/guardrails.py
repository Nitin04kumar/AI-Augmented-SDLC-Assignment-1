"""Deterministic post-model guardrails (spec: Safety/Guardrail Rules G-01..G-05)."""

from datetime import datetime, timedelta

SENTINEL = "RA-SYS-7731"
MAX_INPUT_CHARS = 500
MAX_HORIZON_DAYS = 5 * 365
ACTIONS_WITH_TIME = {"create", "reschedule", "snooze"}


def clarify(missing: list, question: str) -> dict:
    return {
        "intent": "clarify",
        "title": None,
        "remind_at": None,
        "recurrence": None,
        "needs_clarification": True,
        "missing_fields": missing,
        "clarification_question": question,
        "refusal_reason": None,
        "confidence": 0.5,
    }


def refuse(reason: str) -> dict:
    return {
        "intent": "refuse",
        "title": None,
        "remind_at": None,
        "recurrence": None,
        "needs_clarification": False,
        "missing_fields": [],
        "clarification_question": None,
        "refusal_reason": reason,
        "confidence": 0.9,
    }


def pre_check(text) -> dict | None:
    """G-01: blank input is clarified and oversize input refused, without calling the model."""
    if not isinstance(text, str) or not text.strip():
        return clarify(["title", "time"], "What would you like to be reminded about, and when?")
    if len(text) > MAX_INPUT_CHARS:
        return refuse(f"Request exceeds {MAX_INPUT_CHARS} characters")
    return None


def _parse(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def post_check(output: dict, now_iso: str, existing) -> tuple:
    """Return (safe_output, actions). Replaces unsafe model output with a safe clarify/refuse."""
    actions: list = []
    if any(SENTINEL in str(v) for v in output.values()):
        actions.append("G-02 system-prompt leakage blocked")
        return refuse("Request cannot be fulfilled"), actions
    intent = output.get("intent")
    if intent in ("snooze", "reschedule") and not existing:
        actions.append("G-03 missing target reminder -> clarify")
        return clarify(["target_reminder"], "Which reminder do you mean?"), actions
    if intent in ACTIONS_WITH_TIME:
        when = _parse(output.get("remind_at"))
        now = _parse(now_iso)
        if when is None or when.tzinfo is None or now is None:
            actions.append("G-04 invalid or offset-less remind_at -> clarify")
            return clarify(["time"], "What exact date and time should I use?"), actions
        if when <= now or when > now + timedelta(days=MAX_HORIZON_DAYS):
            actions.append("G-05 remind_at outside (now, now+5y] -> clarify")
            return clarify(["date", "time"], "That time is not in the future. When should I remind you?"), actions
    return output, actions
