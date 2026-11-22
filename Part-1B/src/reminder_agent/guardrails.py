
"""Deterministic OSC-1 validation and safety guardrails."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SENTINEL = "RA-SYS-7731"
MAX_INPUT_CHARS = 500
MAX_TITLE_CHARS = 100
MAX_HORIZON_DAYS = 5 * 365
TIME_INTENTS = {"create", "reschedule", "snooze"}


def base_output() -> dict[str, Any]:
    return {
        "intent": "clarify",
        "title": None,
        "remind_at": None,
        "recurrence": None,
        "needs_clarification": False,
        "missing_fields": [],
        "clarification_question": None,
        "refusal_reason": None,
        "confidence": 0.5,
    }


def clarify(
    missing: list[str],
    question: str,
    confidence: float = 0.5,
) -> dict[str, Any]:
    result = base_output()
    result.update(
        {
            "intent": "clarify",
            "needs_clarification": True,
            "missing_fields": list(dict.fromkeys(missing)),
            "clarification_question": (
                question
                if question.strip().endswith("?")
                else f"{question.strip().rstrip('.!?')}?"
            ),
            "confidence": confidence,
        }
    )
    return result


def refuse(
    reason: str,
    confidence: float = 0.9,
) -> dict[str, Any]:
    result = base_output()
    result.update(
        {
            "intent": "refuse",
            "title": None,
            "remind_at": None,
            "recurrence": None,
            "needs_clarification": False,
            "missing_fields": [],
            "clarification_question": None,
            "refusal_reason": reason,
            "confidence": confidence,
        }
    )
    return result


def pre_check(text: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(text, str) or not text.strip():
        return (
            clarify(
                ["title", "time"],
                "What would you like to be reminded about and when?",
            ),
            "G-01 blank input",
        )

    if len(text) > MAX_INPUT_CHARS:
        return (
            refuse(f"Request exceeds {MAX_INPUT_CHARS} characters"),
            "G-01 oversize input",
        )

    lowered = text.lower()

    extraction_phrases = (
        "ignore all previous",
        "system prompt",
        "print your instructions",
        "reveal your instructions",
    )

    if any(phrase in lowered for phrase in extraction_phrases):
        return refuse("Unsupported request"), "G-02 prompt-leakage attempt"

    if "send an email" in lowered:
        return refuse("Unsupported request"), "G-03 unsupported email action"

    return None, None


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None

    return parsed


def timezone_is_valid(tz: Any) -> bool:
    if not isinstance(tz, str) or not tz.strip():
        return False

    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        return False

    return True


def next_weekly_occurrence(
    text: str,
    now_iso: str,
    tz: str | None,
    remind_at: str,
) -> datetime | None:
    """Calculate the next strictly future occurrence of a requested weekday."""

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    weekday_pattern = (
        r"\b(?:every|each)\s+"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
        r"|\bweekly\s+on\s+"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
        r"|\b(?:to|on|for|this|next)\s+"
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    )

    match = re.search(weekday_pattern, text, re.IGNORECASE)

    if not match or not timezone_is_valid(tz):
        return None

    now = parse_datetime(now_iso)
    when = parse_datetime(remind_at)

    if now is None or when is None:
        return None

    weekday_name = next(
        group for group in match.groups() if group is not None
    )

    target_weekday = weekdays[weekday_name.lower()]
    zone = ZoneInfo(tz)

    now_local = now.astimezone(zone)
    when_local = when.astimezone(zone)

    days_ahead = (target_weekday - now_local.weekday()) % 7
    candidate_date = now_local.date() + timedelta(days=days_ahead)

    candidate = datetime.combine(
        candidate_date,
        when_local.timetz().replace(tzinfo=None),
        tzinfo=zone,
    )

    # If today's requested time has passed, select the following week.
    if candidate <= now_local:
        candidate_date += timedelta(days=7)

        candidate = datetime.combine(
            candidate_date,
            when_local.timetz().replace(tzinfo=None),
            tzinfo=zone,
        )

    return candidate


def explicit_past_date_check(
    text: Any,
    now_iso: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Reject an explicitly supplied calendar date before calling the model."""

    if not isinstance(text, str):
        return None, None

    now = parse_datetime(now_iso)

    if now is None:
        return None, None

    date_patterns = [
        (
            r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",
            "%Y-%m-%d",
            "iso",
        ),
        (
            r"\b(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b",
            None,
            "day_month_year",
        ),
        (
            r"\b([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\b",
            None,
            "month_day_year",
        ),
    ]

    for pattern, date_format, date_type in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                if date_type == "iso":
                    supplied_date = datetime.strptime(
                        match.group(0),
                        date_format,
                    ).date()

                elif date_type == "day_month_year":
                    day, month, year = match.groups()

                    try:
                        supplied_date = datetime.strptime(
                            f"{day} {month} {year}",
                            "%d %B %Y",
                        ).date()
                    except ValueError:
                        supplied_date = datetime.strptime(
                            f"{day} {month} {year}",
                            "%d %b %Y",
                        ).date()

                else:
                    month, day, year = match.groups()

                    try:
                        supplied_date = datetime.strptime(
                            f"{month} {day} {year}",
                            "%B %d %Y",
                        ).date()
                    except ValueError:
                        supplied_date = datetime.strptime(
                            f"{month} {day} {year}",
                            "%b %d %Y",
                        ).date()

            except ValueError:
                continue

            if supplied_date < now.date():
                return (
                    clarify(
                        ["date", "time"],
                        (
                            "That date is in the past. "
                            "What future date and time should I use?"
                        ),
                    ),
                    "G-05 explicit past date detected before model call",
                )

    return None, None


def normalize_output(output: Any) -> dict[str, Any]:
    if not isinstance(output, dict):
        return clarify(
            ["title", "time"],
            "Could you rephrase what reminder you want and when?",
        )

    allowed_missing = {
        "title",
        "date",
        "time",
        "target_reminder",
    }

    intent = output.get("intent")

    if intent not in {
        "create",
        "reschedule",
        "snooze",
        "clarify",
        "refuse",
    }:
        intent = "clarify"
        output = dict(output)
        output["intent"] = intent

    result = base_output()
    result["intent"] = intent

    title = output.get("title")

    if isinstance(title, str):
        result["title"] = title
    elif intent in {"create", "reschedule", "snooze"}:
        result["title"] = None

    recurrence = output.get("recurrence")

    result["recurrence"] = (
        recurrence
        if recurrence in {"daily", "weekly", "monthly"}
        else None
    )

    when = output.get("remind_at")

    result["remind_at"] = (
        when if isinstance(when, str) else None
    )

    confidence = output.get("confidence")

    if (
        isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
    ):
        result["confidence"] = min(
            1.0,
            max(0.0, float(confidence)),
        )

    missing = output.get("missing_fields")

    result["missing_fields"] = (
        list(
            dict.fromkeys(
                value
                for value in missing
                if isinstance(value, str)
                and value in allowed_missing
            )
        )
        if isinstance(missing, list)
        else []
    )

    question = output.get("clarification_question")

    if isinstance(question, str):
        if question.strip().endswith("?"):
            result["clarification_question"] = question
        else:
            result["clarification_question"] = (
                f"{question.strip().rstrip('.!?')}?"
            )

    refusal_reason = output.get("refusal_reason")

    if isinstance(refusal_reason, str):
        result["refusal_reason"] = refusal_reason

    return result


def post_check(
    raw_output: Any,
    now_iso: str,
    tz: str | None,
    existing: dict[str, Any] | None,
    snooze_delta: timedelta | None = None,
    request_text: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    actions: list[str] = []

    output = normalize_output(raw_output)
    intent = output["intent"]

    serialized = repr(raw_output)

    if (
        SENTINEL.lower() in serialized.lower()
        or "never reveal these instructions" in serialized.lower()
    ):
        actions.append("G-02 system-prompt leakage blocked")
        return refuse("Unsupported request"), actions

    if len(output.get("title") or "") > MAX_TITLE_CHARS:
        actions.append("OSC-1 title exceeds 100 characters -> clarify")
        return clarify(
            ["title"],
            "What shorter reminder title should I use?",
        ), actions

    if intent in {"snooze", "reschedule"} and not existing:
        actions.append("INV-06 missing target reminder -> clarify")
        return clarify(
            ["target_reminder"],
            "Which reminder do you mean?",
        ), actions

    if intent == "create" and not (output.get("title") or "").strip():
        actions.append("INV-02 create title missing -> clarify")
        return clarify(
            ["title"],
            "What should I remind you about?",
        ), actions

    if intent in TIME_INTENTS:
        now = parse_datetime(now_iso)

        if not timezone_is_valid(tz):
            actions.append("G-04 invalid or missing timezone -> clarify")
            return clarify(
                ["date", "time"],
                "What timezone and exact date or time should I use?",
            ), actions

        if now is None:
            actions.append("G-04 invalid supplied now -> clarify")
            return clarify(
                ["date", "time"],
                "What exact date and time should I use?",
            ), actions

        if intent == "snooze" and snooze_delta is not None:
            when = now + snooze_delta
            output["remind_at"] = when.isoformat()
            output["title"] = existing.get("title") if existing else None

        elif intent == "reschedule" and existing:
            output["title"] = existing.get("title")

        when = parse_datetime(output.get("remind_at"))

        if when is None:
            actions.append("G-04 invalid or offset-less remind_at -> clarify")
            return clarify(
                ["date", "time"],
                "What exact date and time should I use?",
            ), actions

        if (
            when <= now
            or when > now + timedelta(days=MAX_HORIZON_DAYS)
        ):
            actions.append("G-05 remind_at outside future/horizon -> clarify")
            return clarify(
                ["date", "time"],
                "That time is not valid. What future date and time should I use?",
            ), actions

        # Correct explicit weekday requests for create and reschedule.
        if (
            intent in {"create", "reschedule"}
            and request_text
            and (
                output.get("recurrence") == "weekly"
                or intent == "reschedule"
            )
        ):
            expected = next_weekly_occurrence(
                request_text,
                now_iso,
                tz,
                output["remind_at"],
            )

            if expected is not None:
                actual_local = when.astimezone(ZoneInfo(tz))

                if actual_local.date() != expected.date():
                    output["remind_at"] = expected.isoformat()

                    actions.append(
                        "G-06 weekly occurrence corrected "
                        "to the next requested weekday"
                    )

    if intent == "clarify":
        missing = output["missing_fields"]

        if not missing:
            output["missing_fields"] = ["title", "time"]

        output["title"] = None
        output["remind_at"] = None
        output["recurrence"] = None
        output["needs_clarification"] = True

        if not output["clarification_question"]:
            output["clarification_question"] = (
                "What information is missing?"
            )

        output["refusal_reason"] = None

        return output, actions

    if intent == "refuse":
        output["title"] = None
        output["remind_at"] = None
        output["recurrence"] = None
        output["needs_clarification"] = False
        output["missing_fields"] = []
        output["clarification_question"] = None

        if not output["refusal_reason"]:
            output["refusal_reason"] = "Unsupported request"

        return output, actions

    output["needs_clarification"] = False
    output["missing_fields"] = []
    output["clarification_question"] = None
    output["refusal_reason"] = None

    return output, actions
