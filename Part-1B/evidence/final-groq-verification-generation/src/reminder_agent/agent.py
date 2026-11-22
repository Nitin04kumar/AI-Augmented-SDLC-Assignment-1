
"""Reminder request orchestration."""

from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

from .guardrails import (
    clarify,
    explicit_past_date_check,
    post_check,
    pre_check,
)
from .llm import extract_json

PROMPT_FILE = Path(__file__).resolve().parents[2] / "prompts" / "system.md"


def build_user_message(
    text: str,
    now_iso: str,
    tz: str | None,
    existing,
) -> str:
    return json.dumps(
        {
            "text": text,
            "now": now_iso,
            "timezone": tz,
            "existing_reminder": existing,
        },
        ensure_ascii=False,
    )


def parse_request(
    text,
    now_iso,
    tz,
    existing_reminder,
    client,
) -> dict:
    # Run basic input and security checks first.
    early, action = pre_check(text)

    if early is not None:
        actions = [action] if action else ["pre-check"]

        return {
            "output": early,
            "raw": "",
            "actions": actions,
        }

    # Reject explicitly supplied past dates before calling the AI model.
    early, action = explicit_past_date_check(text, now_iso)

    if early is not None:
        actions = [action] if action else ["G-05 past-date check"]

        return {
            "output": early,
            "raw": "",
            "actions": actions,
        }

    # Detect snooze duration for deterministic calculation.
    snooze_delta = None

    snooze_match = re.search(
        r"\bsnooze\b.*\b(\d+)\s+(minute|minutes|hour|hours)\b",
        str(text).lower(),
    )

    if snooze_match:
        amount = int(snooze_match.group(1))

        snooze_delta = (
            timedelta(minutes=amount)
            if "minute" in snooze_match.group(2)
            else timedelta(hours=amount)
        )

    # Send the request to the model only after pre-checks pass.
    system = PROMPT_FILE.read_text(encoding="utf-8")

    raw = client.complete(
        system,
        build_user_message(
            text,
            now_iso,
            tz,
            existing_reminder,
        ),
    )

    parsed = extract_json(raw)

    if parsed is None:
        output = clarify(
            ["title", "time"],
            "Could you rephrase what reminder you want and when?",
        )

        return {
            "output": output,
            "raw": raw,
            "actions": [
                "unparseable model output -> safe clarification"
            ],
        }

    # Apply deterministic post-model validation.
    output, actions = post_check(
        parsed,
        now_iso,
        tz,
        (
            existing_reminder
            if isinstance(existing_reminder, dict)
            else None
        ),
        snooze_delta,
        request_text=text,
    )

    # Remove unsupported instructions from the generated title.
    title = output.get("title")

    if isinstance(title, str):
        lowered_title = title.lower()

        if (
            "delete " in lowered_title
            or "delete all" in lowered_title
            or "sending email" in lowered_title
        ):
            actions.append(
                "G-03 unsupported instruction removed from title"
            )

            output["title"] = re.sub(
                r"\b(?:also\s+)?delete\b.*$",
                "",
                title,
                flags=re.I,
            ).strip(" ,.")

            if not output["title"]:
                output["title"] = "Reminder"

    return {
        "output": output,
        "raw": raw,
        "actions": actions,
    }
