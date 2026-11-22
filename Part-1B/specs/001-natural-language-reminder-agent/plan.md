# Implementation Plan: Natural-Language Reminder Agent

**Branch**: `001-natural-language-reminder-agent` | **Date**: 2026-11-22

**Input**: Feature specification from [spec.md](./spec.md)

## Summary

Implement a Python 3.10+ command-line reminder parser that converts natural-language requests into exactly the OSC-1 JSON object. The implementation will keep model interpretation separate from deterministic safety validation: `agent.py` orchestrates pre-checks, model use, JSON extraction, and post-checks; `guardrails.py` enforces deterministic safety rules; `llm.py` provides Anthropic and OpenAI-compatible clients; `cli.py` owns the public CLI contract; and `__main__.py` provides module entry.

The runtime must use only the Python standard library. Anthropic and OpenAI-compatible providers will use HTTPS and environment-provided secrets. The mock provider is permitted only for offline harness plumbing and is not evaluation evidence. No reminder persistence or delivery is in scope.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Python standard library only; `urllib`, `argparse`, `json`, `datetime`, `zoneinfo`, `re`, and `calendar` as needed

**Development Dependencies**: pytest, ruff, bandit, and the existing harness dependencies

**Target Platform**: Linux CLI

**Project Type**: Python module and command-line application

**Performance Goals**: One bounded model call for an accepted, non-overlong request; no explicit throughput target

**Constraints**: Exact OSC-1 output, deterministic guardrails, no secrets in source, no prompt disclosure, no persistence or delivery, protected evaluation files unchanged

**Scale/Scope**: Single request parsing for one CLI invocation

## Constitution Check

- **Contract-Bounded Behaviour**: every returned object is checked against OSC-1 and structural/behavioral invariants.
- **Deterministic Guardrails**: model text is untrusted and every model result is post-checked.
- **Prompt-Injection Resistance**: user text is serialized as data and unsupported instructions are ignored or refused.
- **Secret Management**: API keys come only from environment variables and are never logged or persisted.
- **Independent Evaluation**: dataset, schema, thresholds, and evaluators remain read-only; thresholds are declared before evaluation.
- **Failure Classification**: `ModelServiceError` is reported separately and distinguished from CLI/application failures.
- **Stack and Quality**: Python 3.10+, standard library runtime, ruff, bandit, and pytest.

No unresolved constitution violations are identified.

## Project Structure

### Documentation (this feature)

```text
specs/001-natural-language-reminder-agent/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── cli-contract.md
```

### Application modules

```text
src/reminder_agent/
├── __init__.py
├── __main__.py
├── agent.py
├── guardrails.py
├── llm.py
└── cli.py

prompts/
└── system.md
```

## Architecture

### 1. CLI layer (`src/reminder_agent/cli.py`)

- Parse `text`, `--now`, `--tz`, and `--existing`.
- Default `--now` only when the caller does not supply it; no supplied `now` may be silently replaced by a machine-derived value in core parsing.
- Parse `--existing` as JSON and retain it for snooze/reschedule checks.
- Print exactly one OSC-1 object to stdout on application success.
- Report `ModelServiceError` distinctly and do not print an OSC-1 object for a model-service failure.
- Invoke `parse_request` and return a process exit status.

### 2. Agent orchestration (`src/reminder_agent/agent.py`)

- Pre-check blank and overlong input before any model call.
- Load `prompts/system.md` only after pre-check success.
- Serialize `text`, `now`, `timezone`, and `existing_reminder` as a JSON user message.
- Call `client.complete(system, user)`.
- Extract the first candidate JSON object, tolerating fences or surrounding prose.
- Convert unparseable model output to a safe clarification.
- Post-check the result for leakage, target-reminder requirements, valid offsets, horizon limits, and future time.
- Return `{"output", "raw", "actions"}`.

### 3. Guardrails (`src/reminder_agent/guardrails.py`)

- Implement G-01 through G-05 deterministically.
- Preserve exact allowed fields and values for every clarified or refused result.
- Never trust title text or reminder times produced by the model before validation.
- Record guardrail actions so evaluation and diagnostics can explain changes.

### 4. LLM provider layer (`src/reminder_agent/llm.py`)

- Select `anthropic`, `openai`, or `mock` through `REMINDER_PROVIDER`.
- Read all credentials from environment variables.
- Restrict network endpoints to HTTPS or loopback localhost for OpenAI-compatible providers.
- Retry only transient 429/5xx failures.
- Raise `ModelServiceError` for authentication, HTTP, network, quota, timeout, and malformed provider response failures.
- Expose `complete(system, user) -> str` and provider diagnostics without secrets.

### 5. Prompt (`prompts/system.md`)

- Define OSC-1 fields and allowed values.
- Treat the user JSON's `text` as data, not instructions.
- Require timezone offsets, next-future recurrence behavior, snooze relative to `now`, and supported-action limitations.
- Include the sentinel solely for leakage testing; never copy prompt or sentinel content into model-derived output fields.

## Time and Timezone Design

- Parse supplied `now_iso` as an ISO-8601 datetime with a UTC offset.
- Interpret supplied `tz` with `zoneinfo.ZoneInfo`; missing or invalid timezone produces clarification rather than a scheduled output.
- Relative dates and recurrence use only supplied `now` and `tz`, never `datetime.now()`.
- Midnight means the next 00:00 in the supplied timezone.
- Today at a time equal to or earlier than `now` requires clarification.
- Recurrence chooses the next strictly future occurrence.
- Snooze adds the requested duration to `now`, not the existing reminder's old time.
- Scheduled results require a timezone offset, `when > now`, and `when <= now + 1825 days` (5 x 365 days).

## Data Flow

1. CLI validates argument shape and parses existing-reminder JSON.
2. `parse_request` performs G-01 blank/oversize checks.
3. The system prompt and a JSON-serialized context are sent to the selected model client.
4. `extract_json` obtains at most one JSON object candidate.
5. If parsing fails, the agent returns a safe clarification.
6. Guardrails validate intent, existing reminder, time offset, horizon, and leakage.
7. The CLI prints exactly the OSC-1 object.

## Validation Strategy

### Unit coverage

- G-01 blank and >500-character branches without model calls.
- Exact 500-character acceptance and 501-character refusal boundaries.
- G-02 sentinel/prompt leakage refusal.
- G-03 unsupported actions and missing target-reminder clarification.
- G-04 malformed and offset-less times.
- G-05 now/past/five-year-limit boundaries.
- OSC-1 title boundaries of exactly 100 and 101 characters.
- JSON extraction, including fenced and prose-wrapped JSON.
- OSC-1 passthrough and deterministic guardrail transformations.

### Lint and security

- `python -m ruff check src tests .harness --config .harness/ruff.toml`
- `python -m bandit -r src -ll`
- `python -m pytest tests -q`

### Independent evaluation

Before evaluation, lock the protected inputs:

```bash
python .harness/run_eval.py --lock
```

Run mock only for harness plumbing:

```bash
REMINDER_PROVIDER=mock python .harness/run_eval.py --label initial --repeats 3
```

Run real evidence only with a real provider:

```bash
REMINDER_PROVIDER=anthropic ANTHROPIC_API_KEY=... python .harness/run_eval.py --label initial --repeats 3
# or
REMINDER_PROVIDER=openai OPENAI_API_KEY=... python .harness/run_eval.py --label initial --repeats 3
```

## Protected Files

Implementation work is confined to `src/` and `prompts/`. The following are read-only:

- `tests/`
- `evals/`
- `.harness/`
- `reference-implementation/`
- `specs/`
- existing thresholds and output schema

## Risk Considerations

- Model JSON drift: extraction and OSC-1/post-model validation prevent extra fields or invalid values.
- Time ambiguity: supplied `now` and timezone are authoritative; invalid timezone data is never inferred.
- Prompt injection: unsupported instructions in user text are ignored or refused.
- Service failures: provider failures remain distinguishable from application and evaluation failures.
- Provider nondeterminism: repeated real-provider runs require the declared thresholds and should be interpreted with the EVAL-4 service-error rule.

## Done When

- The application package and prompt exist under the allowed paths.
- The unit suite passes.
- Lint and security gates pass.
- The locked harness evaluates OSC-1, invariants, safety properties, and semantic quality.
- EVAL-1 through EVAL-4 are reported exactly from the unchanged harness and thresholds.
