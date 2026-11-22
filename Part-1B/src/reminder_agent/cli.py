"""Command-line interface for the Natural-Language Reminder Agent."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .agent import parse_request
from .guardrails import clarify
from .llm import ModelServiceError, get_client


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reminder_agent")
    parser.add_argument("text")
    parser.add_argument("--now", default=None, help="ISO-8601 reference timestamp")
    parser.add_argument("--tz", default=None, help="Timezone name")
    parser.add_argument("--existing", default=None, help="Existing reminder JSON")
    args = parser.parse_args(argv)

    now_iso = args.now
    if now_iso is None:
        now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

    existing = None
    if args.existing is not None:
        try:
            existing = json.loads(args.existing)
        except json.JSONDecodeError:
            result = clarify(["target_reminder"], "Which reminder do you mean?")
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
            return 0

    if not isinstance(existing, dict):
        existing = None

    try:
        client = get_client()
        result = parse_request(args.text, now_iso, args.tz, existing, client)
    except ModelServiceError as exc:
        print(f"model service failure: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(result["output"], ensure_ascii=False, separators=(",", ":")))
    return 0
