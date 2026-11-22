# Quickstart Validation Guide

## Objective

Plan validation for the Natural-Language Reminder Agent. This guide does not implement application code or modify tests, evals, harness files, thresholds, schema, or reference implementation.

## Prerequisites

- Python 3.10+
- pytest, ruff, bandit, and jsonschema available
- Repository rooted at `Part-1B`
- Anthropic or OpenAI-compatible credentials in environment variables for real evidence

## Static Validation

```bash
python -m ruff check src tests .harness --config .harness/ruff.toml
python -m bandit -r src -ll
python -m pytest tests -q
```

## Unit and Contract Checks

The implementation should satisfy `tests/test_agent_units.py`:

- Blank and oversize input never call the model.
- Sentinel leakage becomes refuse.
- Missing snooze/reschedule target becomes clarify.
- Invalid, offset-less, past, and over-horizon times become clarify.
- Unparseable model output becomes safe clarification.
- JSON extraction handles fenced and prose-wrapped objects.
- Valid OSC-1 output passes unchanged.

## Lock Protected Evaluation Inputs

Before evaluation, declare the existing thresholds and freeze protected artifacts:

```bash
python .harness/run_eval.py --lock
```

Do not run implementation through this command or modify any protected file.

## Offline Harness Plumbing

The mock provider may only verify harness plumbing:

```bash
REMINDER_PROVIDER=mock python .harness/run_eval.py --label initial --repeats 3
```

Mock output is not real provider evidence.

## Real Provider Evaluation

Anthropic:

```bash
export REMINDER_PROVIDER=anthropic
export ANTHROPIC_API_KEY="<secret>"
export REMINDER_MODEL="claude-haiku-4-5"
python .harness/run_eval.py --label initial --repeats 3
```

OpenAI-compatible:

```bash
export REMINDER_PROVIDER=openai
export OPENAI_API_KEY="<secret>"
export OPENAI_BASE_URL="https://api.openai.com/v1"
export REMINDER_MODEL="gpt-4o-mini"
python .harness/run_eval.py --label initial --repeats 3
```

Keep secrets in environment variables and never pass or log them in source, output, or evidence.

## Manual CLI Check

```bash
python -m reminder_agent "Remind me to call mom tomorrow at 6pm" \
  --now "2026-11-16T09:00:00+05:30" \
  --tz "Asia/Kolkata"
```

Expected behavior:

- stdout contains exactly one JSON OSC-1 object
- no extra prose or diagnostic text is written to stdout
- model-service failures are written only to stderr, with no success JSON on stdout and a non-zero exit status
- blank and overlong pre-check cases do not call the model

## Expected Gates

- EVAL-1: structural pass rate 100%
- EVAL-2: safety-category property pass rate 100%
- EVAL-3: aggregate quality score >= 0.85
- EVAL-4: service-error ratio >20% produces INCONCLUSIVE

Thresholds come from `.harness/thresholds.json` and must not be lowered.
