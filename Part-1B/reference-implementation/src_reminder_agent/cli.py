"""Usage: python -m reminder_agent "Remind me to call mom tomorrow at 6pm" [--now ISO] [--tz TZ]"""

import argparse
import json
import sys
from datetime import datetime

from reminder_agent.agent import parse_request
from reminder_agent.llm import ModelServiceError, get_client


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="reminder_agent")
    ap.add_argument("text")
    ap.add_argument("--now", default=datetime.now().astimezone().isoformat(timespec="seconds"))
    ap.add_argument("--tz", default="Asia/Kolkata")
    ap.add_argument("--existing", default=None, help="JSON of the existing reminder")
    args = ap.parse_args(argv)
    existing = json.loads(args.existing) if args.existing else None
    try:
        result = parse_request(args.text, args.now, args.tz, existing, get_client())
    except ModelServiceError as exc:
        print(json.dumps({"error": f"model service failure: {exc}"}), file=sys.stderr)
        return 3
    print(json.dumps(result["output"], indent=2))
    return 0
