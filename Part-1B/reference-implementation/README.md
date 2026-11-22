# Reference implementation (NOT your evidence)

Used only to verify the harness plumbing. `llm.py` contains a `mock` provider (regex stand-in, not an AI model)
that is useful ONLY for dry-running `.harness/run_eval.py`. Real evaluation evidence must use a real model
(REMINDER_PROVIDER=anthropic or openai-compatible) and the code from YOUR `/speckit.implement` run.

Dry run:
    mkdir -p /tmp/refb && cp -r ../. /tmp/refb && cd /tmp/refb
    cp -r reference-implementation/src_reminder_agent src/reminder_agent
    cp reference-implementation/system.md prompts/system.md
    python .harness/run_eval.py --lock && python .harness/run_eval.py --label dry-run
