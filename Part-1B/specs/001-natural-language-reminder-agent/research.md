# Research: Natural-Language Reminder Agent

## Decision Record

### Decision: Standard-library-only Python runtime

Use Python 3.10+ and standard-library modules only for application code. Network access is implemented with `urllib.request`; CLI parsing uses `argparse`; JSON uses `json`; timezone handling uses `zoneinfo`; and date arithmetic uses `datetime` and `timedelta`.

**Rationale**: The constitution and assignment seed explicitly require Python 3.10+ and prohibit non-standard runtime dependencies. The implementation remains portable and easy to lint and evaluate.

**Alternatives considered**:
- Third-party HTTP or CLI libraries: rejected because they add dependencies and are unnecessary for the seed contract.
- Third-party timezone libraries: rejected because `zoneinfo` is available in Python 3.10+ and is sufficient.

### Decision: Orchestrator and deterministic post-validation split

Keep model interaction in `llm.py`, orchestration in `agent.py`, and deterministic rules in `guardrails.py`.

**Rationale**: This makes model output untrusted by design and allows unit tests to verify pre-check, extraction, and post-check behavior without real model calls.

**Alternatives considered**:
- LLM-only parsing: rejected because prompt instructions alone cannot enforce the strict schema and deterministic boundaries.
- Time parsing inside the provider client: rejected because providers should only transport requests and responses; domain validation belongs in the agent and guardrail layers.

### Decision: Supplied context is authoritative

Resolve all relative dates and snooze durations using `now_iso` and `tz`. Never call the machine clock in the core parser.

**Rationale**: FR-01 and the clarifications require deterministic reference behavior. The harness supplies fixed test timestamps, so implicit local-clock access would make results nondeterministic.

**Alternatives considered**:
- Use machine-local time for relative expressions: rejected by the specification.
- Infer timezone from `now` without an explicit valid timezone: rejected by G-04/G-05 and INV-02.

### Decision: Existing reminder is required for snooze and reschedule

Model output requesting `snooze` or `reschedule` becomes clarify with `missing_fields=["target_reminder"]` when no existing reminder is supplied.

**Rationale**: INV-06 explicitly forbids these operations without target context.

**Alternatives considered**:
- Allow target selection by title alone: rejected because the core API accepts only an optional existing reminder and cannot persist or search reminders.
- Preserve a snooze/reschedule with fabricated context: rejected because it could modify the wrong reminder and violates INV-06.

### Decision: Safe clarification for unparseable model output

When extraction cannot find valid JSON or the model result cannot be parsed, return a clarify object rather than an application exception.

**Rationale**: The specification requires unparseable model text to result in a safe clarification.

**Alternatives considered**:
- Return raw model text: rejected because OSC-1 requires a strict JSON object and exact field set.
- Refuse all unparseable output: clarification is the safer and simpler contract-compliant fallback.

### Decision: Provider implementation and failure classification

Support Anthropic and OpenAI-compatible HTTP APIs, with `REMINDER_PROVIDER` selecting the client and credentials read only from environment variables. Raise `ModelServiceError` for network, HTTP, auth, quota, timeout, and malformed provider response failures.

**Rationale**: The assignment seed requires provider selection, environment secrets, HTTPS, retries, and separate service failures.

**Alternatives considered**:
- Hard-code provider credentials or accept API keys in CLI arguments: rejected by the secret-management constitution.
- Continue with a clarification on service failure: rejected because the harness must distinguish model-service failures from application failures.

### Decision: Five-year horizon

Validate every scheduled action against `now < remind_at <= now + 5 * 365 days`.

**Rationale**: INV-02 is explicit. A leap-aware exact `365*5` is not required by the harness and may differ in interpretation; the property evaluator uses `timedelta(days=5 * 365)`.

**Alternatives considered**:
- Exact leap-year calendar arithmetic: not selected because the read-only property evaluator compares against exactly five times 365 days.
- No upper bound: rejected by INV-02.

## Open Questions Resolved by the Specification

- Midnight: next 00:00 in the supplied timezone.
- Equal or past "today": clarify, never schedule.
- Recurrence: next strictly future occurrence.
- Snooze reference: `now`, not existing reminder time.
- Relative dates: supplied `now` and timezone only.
- Missing or invalid timezone: do not schedule without an offset; clarify.
- Unparseable model output: safe clarify.
- Snooze/reschedule with no existing reminder: clarify `target_reminder`.

## Verification Strategy

The implementation is valid if it passes:

- Unit tests in `tests/test_agent_units.py`.
- ruff and bandit checks.
- The protected integrity lock.
- OSC-1 structural validation.
- All defined invariant and case-property checks.
- Semantic aggregate quality and service-error thresholds.

Real provider runs are evidence only; `mock` is limited to offline harness plumbing.
