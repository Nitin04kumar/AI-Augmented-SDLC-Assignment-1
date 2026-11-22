"""Model provider clients and deterministic JSON extraction."""

from __future__ import annotations

import calendar
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta


class ModelServiceError(Exception):
    """A model provider, network, quota, or response failure."""


def _post(url: str, headers: dict[str, str], body: dict, timeout: int = 60, retries: int = 2) -> dict:
    allowed = url.startswith("https://") or url.startswith("http://localhost") or url.startswith("http://127.0.0.1")
    if not allowed:
        raise ModelServiceError("Refusing non-HTTPS endpoint")

    data = json.dumps(body).encode("utf-8")
    last_error = "unknown model service error"
    for attempt in range(retries + 1):
        # Some API gateways (including Groq's Cloudflare front door) reject
        # urllib's default Python-urllib User-Agent. Copy caller headers so the
        # original dictionary is not mutated, then provide an explicit agent.
        request_headers = dict(headers)
        request_headers.setdefault("User-Agent", "curl/8.5.0")
        request = urllib.request.Request(
            url,
            data=data,
            headers=request_headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 529):
                break
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = str(exc)
        if attempt < retries:
            time.sleep(1.5 * (attempt + 1))
    raise ModelServiceError(last_error)


class AnthropicClient:
    def __init__(self) -> None:
        self.key = os.environ.get("ANTHROPIC_API_KEY")
        self.model = os.environ.get("REMINDER_MODEL", "claude-haiku-4-5")
        self.temperature = float(os.environ.get("REMINDER_TEMPERATURE", "0.3"))
        if not self.key:
            raise ModelServiceError("ANTHROPIC_API_KEY is not set")

    def describe(self) -> dict:
        return {"provider": "anthropic", "model": self.model, "temperature": self.temperature}

    def complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": self.temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        result = _post("https://api.anthropic.com/v1/messages", headers, body)
        try:
            content = result["content"]
            return "".join(item.get("text", "") for item in content)
        except (KeyError, TypeError) as exc:
            raise ModelServiceError("Unexpected Anthropic response shape") from exc


class OpenAICompatClient:
    def __init__(self) -> None:
        self.key = os.environ.get("OPENAI_API_KEY", "")
        self.base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.environ.get("REMINDER_MODEL", "gpt-4o-mini")
        self.temperature = float(os.environ.get("REMINDER_TEMPERATURE", "0.3"))

    def describe(self) -> dict:
        return {
            "provider": "openai-compatible",
            "base_url": self.base,
            "model": self.model,
            "temperature": self.temperature,
        }

    def complete(self, system: str, user: str) -> str:
        body = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        headers = {"content-type": "application/json"}
        if self.key:
            headers["authorization"] = f"Bearer {self.key}"
        result = _post(f"{self.base}/chat/completions", headers, body)
        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelServiceError("Unexpected OpenAI-compatible response shape") from exc


def base_output(**changes):
    result = {
        "intent": "clarify",
        "title": None,
        "remind_at": None,
        "recurrence": None,
        "needs_clarification": False,
        "missing_fields": [],
        "clarification_question": None,
        "refusal_reason": None,
        "confidence": 0.7,
    }
    result.update(changes)
    return result


def mock_complete(user_json: str) -> str:
    context = json.loads(user_json)
    text = str(context.get("text", "")).strip()
    lowered = text.lower()
    now = datetime.fromisoformat(context["now"])
    existing = context.get("existing_reminder")

    if "ignore all previous" in lowered or "system prompt" in lowered:
        return json.dumps(base_output(intent="refuse", refusal_reason="Unsupported request"))
    if "send an email" in lowered:
        return json.dumps(base_output(intent="refuse", refusal_reason="Unsupported request"))

    snooze_match = re.search(r"\bsnooze\b.*\b(\d+)\s+(minute|minutes|hour|hours)\b", lowered)
    if snooze_match:
        amount = int(snooze_match.group(1))
        delta = timedelta(minutes=amount) if "minute" in snooze_match.group(2) else timedelta(hours=amount)
        return json.dumps(
            base_output(
                intent="snooze",
                title=existing.get("title") if existing else None,
                remind_at=(now + delta).isoformat(),
                needs_clarification=False,
            )
        )

    in_match = re.search(r"\bin\s+(\d+)\s+(minute|minutes|hour|hours)\b", lowered)
    if in_match:
        amount = int(in_match.group(1))
        delta = timedelta(minutes=amount) if "minute" in in_match.group(2) else timedelta(hours=amount)
        title = extract_title(text)
        if not title:
            return json.dumps(base_output(intent="clarify", needs_clarification=True, missing_fields=["title"],
                                          clarification_question="What should I remind you about?"))
        return json.dumps(base_output(intent="create", title=title, remind_at=(now + delta).isoformat()))

    day = None
    if "tomorrow" in lowered:
        day = now.date() + timedelta(days=1)
    elif "today" in lowered:
        day = now.date()
    elif "midnight" in lowered:
        day = now.date() + timedelta(days=1)
    else:
        date_match = re.search(r"\bon\s+(\d{1,2})\s+([a-z]+)\s+(\d{4})\b", lowered)
        if date_match:
            month_names = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
            month = month_names.get(date_match.group(2))
            if month:
                day = datetime(int(date_match.group(3)), month, int(date_match.group(1))).date()
        if day is None:
            weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
                        "saturday": 5, "sunday": 6}
            for name, weekday in weekdays.items():
                if name in lowered:
                    ahead = (weekday - now.weekday()) % 7
                    if ahead == 0:
                        ahead = 7
                    day = now.date() + timedelta(days=ahead)
                    break
        if "last day" in lowered:
            if now.month == 12:
                day = datetime(now.year, 12, 31).date()
            else:
                day = datetime(now.year, now.month + 1, 1).date() - timedelta(days=1)

    clock = extract_clock(lowered)
    title = extract_title(text)
    if existing and ("move " in lowered or "reschedule" in lowered):
        title = existing.get("title")

    missing = []
    if not title:
        missing.append("title")
    if day is None:
        missing.append("date")
    if clock is None:
        missing.append("time")
    if missing:
        question_words = []
        if "title" in missing:
            question_words.append("what should I remind you about")
        if "date" in missing or "time" in missing:
            question_words.append("what date and time")
        question = (" and ".join(question_words).capitalize() + "?")
        if not question.strip("?"):
            question = "What date and time should I use?"
        return json.dumps(base_output(intent="clarify", needs_clarification=True,
                                      missing_fields=list(dict.fromkeys(missing)),
                                      clarification_question=question))

    if clock is not None and day is not None:
        scheduled = datetime(day.year, day.month, day.day, clock[0], clock[1], tzinfo=now.tzinfo)
        intent = "reschedule" if existing and ("move " in lowered or "reschedule" in lowered) else "create"
        recurrence = "weekly" if "every" in lowered and "monday" in lowered else None
        return json.dumps(
            base_output(intent=intent, title=title, remind_at=scheduled.isoformat(), recurrence=recurrence)
        )

    return json.dumps(base_output(intent="clarify", needs_clarification=True,
                                  missing_fields=["time"],
                                  clarification_question="What exact date and time should I use?"))


def extract_title(text: str) -> str | None:
    lowered = text.lower()
    match = re.search(r"\bremind\s+(?:me\s+)?(?:to\s+|about\s+)?(.+)$", lowered, re.I)
    body = match.group(1).strip() if match else text.strip()
    body = re.sub(
        r"\b(tomorrow|today|tonight|midnight|every\s+\w+|in\s+\d+\s+(?:minute|minutes|hour|hours)|"
        r"at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?|on\s+\d{1,2}\s+\w+\s+\d{4}|"
        r"on\s+the\s+last\s+day\s+of\s+(?:this|the)\s+month|later|sometime\s+next\s+week)\b",
        " ",
        body,
        flags=re.I,
    )
    body = re.sub(r"\balso\s+delete.*$", "", body, flags=re.I)
    body = " ".join(body.split()).strip(" ,.")
    if not body:
        return None
    return body[:200]


def extract_clock(text: str) -> tuple[int, int] | None:
    if "midnight" in text:
        return (0, 0)
    match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3)
    if period == "pm" and hour < 12:
        hour += 12
    if period == "am" and hour == 12:
        hour = 0
    return (hour, minute)


class MockClient:
    def describe(self) -> dict:
        return {"provider": "mock", "model": "regex-heuristic", "temperature": 0}

    def complete(self, system: str, user: str) -> str:
        del system
        return mock_complete(user)


def extract_json(text: str) -> dict | None:
    cleaned = re.sub(r"```(?:json)?", "", text or "", flags=re.I).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        result = json.loads(cleaned[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    return result if isinstance(result, dict) else None


def get_client():
    provider = os.environ.get("REMINDER_PROVIDER", "mock").lower()
    if provider == "anthropic":
        return AnthropicClient()
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatClient()
    if provider == "mock":
        return MockClient()
    raise ModelServiceError(f"Unknown REMINDER_PROVIDER: {provider}")
