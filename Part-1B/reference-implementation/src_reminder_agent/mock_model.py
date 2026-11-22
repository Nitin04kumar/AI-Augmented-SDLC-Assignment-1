"""Tiny regex 'model' so the harness can be exercised offline. NOT an AI model."""

import calendar
import json
import re
from datetime import datetime, timedelta

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}


def _base(**kw) -> dict:
    out = {
        "intent": "clarify", "title": None, "remind_at": None, "recurrence": None,
        "needs_clarification": False, "missing_fields": [], "clarification_question": None,
        "refusal_reason": None, "confidence": 0.7,
    }
    out.update(kw)
    return out


def _clock(text):
    if "midnight" in text:
        return 0, 0
    m = re.search(r"\bat (\d{1,2})(?::(\d{2}))? ?(am|pm)?\b", text)
    if not m:
        return None
    hour, minute, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ap == "pm" and hour < 12:
        hour += 12
    if ap == "am" and hour == 12:
        hour = 0
    return hour, minute


def _title(text):
    m = re.search(r"remind me (?:to |about )?(.*)", text)
    body = m.group(1) if m else text
    body = re.sub(r"\b(tomorrow|today|tonight|at \S+( ?[ap]m)?|on \d.*|in \d+ \w+|every \w+|"
                  r"on the last.*|at midnight)\b", " ", body)
    body = re.sub(r"\b(i need to|please)\b", " ", body)
    return " ".join(body.split()).strip(" ,.") or None


def respond(user_json: str) -> str:
    ctx = json.loads(user_json)
    text = ctx["text"].lower()
    now = datetime.fromisoformat(ctx["now"])
    existing = ctx.get("existing_reminder")

    if "ignore all previous" in text or "system prompt" in text or "send an email" in text:
        return json.dumps(_base(intent="refuse", refusal_reason="Unsupported request"))

    m = re.search(r"snooze.*?(\d+) ?(minute|hour)", text)
    if m:
        delta = timedelta(minutes=int(m.group(1))) if m.group(2) == "minute" else timedelta(hours=int(m.group(1)))
        title = existing["title"] if existing else None
        return json.dumps(_base(intent="snooze", title=title, remind_at=(now + delta).isoformat()))

    m = re.search(r"in (\d+) (minute|hour)s?", text)
    if m:
        delta = timedelta(minutes=int(m.group(1))) if m.group(2) == "minute" else timedelta(hours=int(m.group(1)))
        return json.dumps(_base(intent="create", title=_title(text), remind_at=(now + delta).isoformat()))

    day = None
    if "tomorrow" in text:
        day = now.date() + timedelta(days=1)
    elif "today" in text:
        day = now.date()
    elif "midnight" in text:
        day = now.date() + timedelta(days=1)
    else:
        m = re.search(r"on (\d{1,2}) (\w+) (\d{4})", text)
        if m and m.group(2) in MONTHS:
            day = datetime(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))).date()
        else:
            for i, name in enumerate(DAYS):
                if name in text:
                    ahead = (i - now.weekday()) % 7 or 7
                    day = now.date() + timedelta(days=ahead)
    clock = _clock(text)
    title = _title(text)
    is_move = "move" in text or "reschedule" in text
    if is_move and existing:
        title = existing["title"]
    missing = [f for f, v in (("title", title), ("date", day), ("time", clock)) if not v and v != 0]
    if day and clock is None and "date" not in missing:
        missing = [f for f in missing if f != "date"]
    if missing or day is None or clock is None:
        return json.dumps(_base(intent="clarify", needs_clarification=True,
                                missing_fields=missing or ["time"],
                                clarification_question="When and what should I remind you about?"))
    when = datetime(day.year, day.month, day.day, clock[0], clock[1], tzinfo=now.tzinfo)
    intent = "reschedule" if is_move else "create"
    rec = "weekly" if "every" in text else None
    return json.dumps(_base(intent=intent, title=title, remind_at=when.isoformat(), recurrence=rec))
