"""Reminder agent: prompt construction -> model call -> JSON parse -> guardrails."""

import json
from pathlib import Path

from reminder_agent import guardrails
from reminder_agent.llm import extract_json

PROMPT_FILE = Path(__file__).resolve().parents[2] / "prompts" / "system.md"


def build_user_message(text, now_iso, tz, existing) -> str:
    return json.dumps(
        {"text": text, "now": now_iso, "timezone": tz, "existing_reminder": existing},
        ensure_ascii=False,
    )


def parse_request(text, now_iso, tz, existing, client) -> dict:
    """Returns {"output": dict|None, "raw": str, "actions": [...]}.

    Raises reminder_agent.llm.ModelServiceError on model-service failure (caller decides).
    """
    early = guardrails.pre_check(text)
    if early is not None:
        return {"output": early, "raw": "", "actions": ["G-01 pre-check short-circuit"]}
    system = PROMPT_FILE.read_text(encoding="utf-8")
    raw = client.complete(system, build_user_message(text, now_iso, tz, existing))
    parsed = extract_json(raw)
    if not isinstance(parsed, dict):
        safe = guardrails.clarify(["title", "time"], "Sorry, could you rephrase your request?")
        return {"output": safe, "raw": raw, "actions": ["unparseable model output -> clarify"]}
    safe, actions = guardrails.post_check(parsed, now_iso, existing)
    return {"output": safe, "raw": raw, "actions": actions}
