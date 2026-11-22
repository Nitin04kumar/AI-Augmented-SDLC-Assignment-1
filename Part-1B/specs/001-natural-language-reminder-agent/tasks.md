# Tasks: Natural-Language Reminder Agent

**Input**: Design documents in `/specs/001-natural-language-reminder-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contract.md, quickstart.md

**Protected inputs**: `evals/dataset.json`, `tests/test_agent_units.py`, `.harness/`, thresholds, and the output schema are read-only.

**Implementation boundary**: All implementation changes are restricted to `src/` and `prompts/`.

## Format: `[ID] [P?] Description`

- **[P]**: Task can proceed independently of other parallel tasks.
- **Every implementation task cites one or more exact requirement IDs.**
- Tasks begin incomplete; no task is marked complete before implementation and verification.

## Pre-Implementation Gate

**Purpose**: Freeze protected evaluation inputs after `/speckit.analyze` and before `/speckit.implement` begins.

- [ ] T056 Run `python .harness/run_eval.py --lock` after `/speckit.analyze` and before any implementation or evaluation run. T056 may create only the required `.harness/protected.lock.json` baseline; no other `.harness/` file may be modified. Leave `evals/dataset.json`, `tests/`, `reference-implementation/`, thresholds, the output schema, and protected specs read-only. (EVAL-1; EVAL-2; EVAL-3)

## Phase 1: Setup

- [ ] T001 Establish the `src/reminder_agent/` package structure and create the implementation module files `agent.py`, `guardrails.py`, `llm.py`, and `cli.py` using Python 3.10+ and the standard library only. (OSC-1)
- [ ] T002 Create `prompts/system.md` with OSC-1 output rules and instructions that treat user text as data rather than instructions. (OSC-1; G-02; G-03; INV-07)
- [ ] T003 [P] Implement the separate package entry point in `src/reminder_agent/__main__.py` so `python -m reminder_agent` invokes `src/reminder_agent/cli.py:main()`. (OSC-1)
- [ ] T004 [P] Implement the separate package exports and metadata in `src/reminder_agent/__init__.py` without adding runtime dependencies. (OSC-1)

## Phase 2: Core Implementation

- [ ] T005 Implement OSC-1 clarification construction in `src/reminder_agent/guardrails.py` with `needs_clarification=true`, unique non-empty `missing_fields`, a question ending in `?`, and null `remind_at`. (INV-03)
- [ ] T006 Implement OSC-1 refusal construction in `src/reminder_agent/guardrails.py` with a refusal reason and null `title` and `remind_at`. (INV-05)
- [ ] T007 Implement non-clarify output normalization so clarification state is false and `missing_fields` is empty. (INV-04)
- [ ] T008 Implement deterministic ISO-8601 parsing in `src/reminder_agent/guardrails.py` and require timezone offsets on every scheduled result. (INV-02; G-04)
- [ ] T009 Implement the five-year horizon check for create, snooze, and reschedule using `now + timedelta(days=1825)`. (INV-02; G-05)
- [ ] T010 Implement the core `parse_request(text, now_iso, tz, existing_reminder, client) -> {"output","raw","actions"}` orchestration in `src/reminder_agent/agent.py`. (OSC-1)
- [ ] T011 Implement pre-model user-context serialization in `src/reminder_agent/agent.py` as JSON containing `text`, `now`, `timezone`, and `existing_reminder`. (G-02; G-03)
- [ ] T012 Implement create-result handling from title plus concrete date/time, resolved against supplied `now` and timezone rather than the machine clock. (FR-01; INV-02)
- [ ] T013 Implement next-midnight resolution as the next 00:00 in the supplied timezone. (FR-01; INV-02)
- [ ] T014 Implement recurrence recognition and next-strictly-future occurrence selection for daily, weekly, and monthly reminders. (FR-06)
- [ ] T015 Implement missing or vague title/date/time clarification behavior. (FR-02; INV-03)
- [ ] T016 Implement snooze handling so the result is `now + duration` and preserves the existing reminder title. (FR-03; INV-02)
- [ ] T017 Implement reschedule handling so the existing reminder title is preserved and a concrete future time is returned. (FR-04; INV-02)
- [ ] T018 Implement missing existing-reminder handling so snooze and reschedule become clarification with `missing_fields=["target_reminder"]`. (INV-06; INV-03)
- [ ] T019 Implement JSON extraction in `src/reminder_agent/llm.py` for fenced JSON and JSON surrounded by prose, with no fallback to arbitrary text. (OSC-1)
- [ ] T020 Implement safe clarification fallback for unparseable model output and retain the raw response only in `raw`. (OSC-1)
- [ ] T066 Implement a deterministic OSC-1 title-length post-check: if a model-produced title exceeds 100 characters, convert the result to clarification with `missing_fields=["title"]`, null `remind_at`, and a question asking for a shorter title. (OSC-1; INV-03)

## Phase 3: Guardrails

- [ ] T021 Implement G-01 blank-input handling before any model call, returning a clarification. (G-01; INV-03)
- [ ] T022 Implement G-01 input-length handling for text longer than 500 characters, returning refuse without a model call. (G-01; INV-05)
- [ ] T023 Implement G-02 system-prompt and sentinel leakage detection across all output fields and return refuse. (G-02; INV-07)
- [ ] T024 Implement G-03 refusal or safe ignoring of sending email, deleting reminders, reminder persistence/delivery, and instructions embedded in user text. (G-03; INV-05)
- [ ] T025 Implement G-04 invalid, malformed, and offset-less `remind_at` conversion to clarification for create, snooze, and reschedule. (G-04; INV-03)
- [ ] T026 Implement G-05 equal-now and past-time conversion to clarification. (G-05; INV-03)
- [ ] T027 Implement over-five-year `remind_at` conversion to clarification for scheduled actions. (INV-02; G-05)
- [ ] T028 Implement missing or invalid timezone handling so no scheduled output is emitted without an offset-bearing time. (INV-02; G-04)
- [ ] T029 Implement prompt-injection-resistant handling that treats user text as untrusted data and never executes or copies embedded instructions into title fields. (G-02; G-03; INV-07)
- [ ] T030 Implement deterministic guardrail action recording in `src/reminder_agent/agent.py` and `src/reminder_agent/guardrails.py` so `actions` explains pre/post-check transformations. (OSC-1)

## Phase 4: Model Integration

- [ ] T031 Implement `ModelServiceError` for HTTP, network, timeout, authentication, quota, and malformed-provider-response failures in `src/reminder_agent/llm.py`. (EVAL-4)
- [ ] T032 Implement provider selection from `REMINDER_PROVIDER=anthropic|openai|mock` in `src/reminder_agent/llm.py` without secrets in source or logs. (EVAL-4)
- [ ] T033 Implement the Anthropic `complete(system, user) -> str` client using `ANTHROPIC_API_KEY` only from the environment. (OSC-1; EVAL-4)
- [ ] T034 [P] Implement the OpenAI-compatible `complete(system, user) -> str` client using `OPENAI_API_KEY` and `OPENAI_BASE_URL` only from the environment. (OSC-1; EVAL-4)
- [ ] T035 Implement HTTPS-only provider requests except permitted loopback endpoints, with retries on 429 and 5xx responses. (EVAL-4)
- [ ] T036 Implement the mock client only as harness plumbing and ensure it is not described or used as real evaluation evidence. (EVAL-1; EVAL-2; EVAL-3)
- [ ] T037 Implement provider diagnostics that do not expose API keys, system prompt content, or the prompt sentinel. (INV-07; EVAL-4)

## Phase 5: CLI

- [ ] T038 Implement CLI argument parsing in `src/reminder_agent/cli.py` for text, `--now`, `--tz`, and JSON `--existing`. When `--now` is omitted, obtain the current local ISO-8601 timestamp once and pass it as supplied context; preserve explicit `--now` values. When `--tz` is omitted or invalid, do not infer or schedule an offset-bearing timestamp and return clarification. (OSC-1; INV-02)
- [ ] T039 Implement CLI parsing of `--existing`: pass valid JSON context into `parse_request` unchanged for target validation; malformed JSON becomes OSC-1 clarification with `missing_fields=["target_reminder"]` and cannot schedule an action. (INV-06; OSC-1)
- [ ] T040 Implement exactly-one-JSON-object stdout behavior for successful CLI parsing with all OSC-1 fields and no extra fields. (OSC-1)
- [ ] T041 Implement only CLI exit-status and error-routing behavior in `src/reminder_agent/cli.py`, keeping module-entry ownership solely in T003's `src/reminder_agent/__main__.py`. (OSC-1; EVAL-4)
- [ ] T042 Implement distinct CLI reporting for `ModelServiceError`: write a safe diagnostic to stderr, emit no success JSON on stdout, and exit with status `3` separate from OSC-1 application output. (OSC-1; EVAL-4)

## Phase 6: Unit Testing

- [ ] T043 Run the existing protected blank-input test in `tests/test_agent_units.py` and verify it returns clarify without calling the model; do not edit the test file. (G-01)
- [ ] T044 Verify both input boundaries: exactly 500 characters are accepted and proceed only to normal model parsing, while 501 characters refuse without a model call. Run the existing protected oversize test and use a temporary uncommitted script outside protected project files only if exactly-500 coverage is unavailable. (G-01)
- [ ] T045 Run the existing protected sentinel-leakage test in `tests/test_agent_units.py` and verify it refuses. (G-02; INV-07)
- [ ] T046 Run the existing protected missing-target test in `tests/test_agent_units.py` and verify snooze/reschedule clarifies with `target_reminder`. (INV-06; INV-03)
- [ ] T047 Run the existing protected G-04/G-05 parameterized test in `tests/test_agent_units.py`; for additional malformed cases, use a temporary uncommitted script outside `tests/`, `evals/`, and `.harness/`. (G-04)
- [ ] T048 Run the existing protected equal-now and past-time checks in `tests/test_agent_units.py` and verify clarification with no scheduled time. (G-05)
- [ ] T049 Verify exactly-at-now, at-now-plus-five-years, and beyond-five-years behavior through the protected parameterized/property checks and, only if needed, a temporary uncommitted script outside protected project files. (INV-02)
- [ ] T050 Verify invalid timezone names and missing timezone offsets through a temporary uncommitted script outside protected project files; do not modify protected tests or schema. (INV-02; G-04)
- [ ] T051 Run the existing protected JSON-extraction and unparseable-output tests in `tests/test_agent_units.py`; do not edit them. (OSC-1)
- [ ] T052 Run the existing protected structural and valid-output passthrough tests in `tests/test_agent_units.py` and verify extra fields are rejected by the read-only schema/harness. (OSC-1)
- [ ] T053 Run the existing snooze/reschedule unit behavior and read-only TC-12/TC-13 dataset cases through the harness or temporary scripts; do not modify `evals/dataset.json` or protected tests. (FR-03; FR-04; INV-02)
- [ ] T054 First run the protected TC-17, TC-18, and TC-19 cases from `evals/dataset.json` plus the existing protected leakage test; only after those pass, use temporary uncommitted scripts outside protected project files for additional prompt-injection probes. (G-02; G-03; INV-07)
- [ ] T055 Run `python -m pytest tests/test_agent_units.py -q` and resolve application failures only under `src/` or `prompts/`. (EVAL-1; EVAL-2)
- [ ] T067 Verify a 100-character title is accepted and a 101-character title becomes clarification with `missing_fields=["title"]` and null `remind_at`, using the protected unit suite or a temporary uncommitted script outside protected project files. (OSC-1; INV-03)
- [ ] T068 Verify malformed `--existing` JSON through the existing protected tests if applicable or a temporary uncommitted script outside protected project files: the result must be an OSC-1 clarification, `missing_fields` must contain `target_reminder`, `remind_at` must be null, and no create, snooze, or reschedule action may be scheduled; do not modify `tests/`, `evals/`, or `.harness/`. (OSC-1; INV-06)

## Phase 7: Final Validation

- [ ] T057 Run the Ruff validation command with `.harness/ruff.toml` and repair only application-source findings. (OSC-1)
- [ ] T058 Run Bandit against `src/` and repair medium/high findings without changing protected files. (G-02; G-03)
- [ ] T059 Run the full existing pytest unit suite and confirm deterministic unit-test coverage passes. (EVAL-1; EVAL-2)
- [ ] T060 Run mock-provider harness plumbing once as an implementation smoke test only; do not treat it as real provider evidence. (EVAL-1; EVAL-2; EVAL-3)
- [ ] T061 Run the real-model evaluation pipeline three times with Anthropic or an OpenAI-compatible provider and environment-only credentials. (EVAL-1; EVAL-2; EVAL-3; EVAL-4)
- [ ] T062 Human review the final evaluation output, review evidence for threshold interpretation and service-error classification, and verify no thresholds or protected artifacts were changed. (EVAL-1; EVAL-2; EVAL-3; EVAL-4)
- [ ] T063 Confirm final structural, safety-property, and aggregate quality thresholds are reported exactly: OSC-1 100%, safety 100%, quality >=0.85. (EVAL-1; EVAL-2; EVAL-3)
- [ ] T064 If more than 20% of cases fail from model-service errors, classify the run as INCONCLUSIVE rather than FAIL and record it separately. (EVAL-4)
- [ ] T065 Snapshot initial/final application evidence under the existing evidence workflow without copying secrets or modifying protected inputs. (EVAL-4)

## Dependencies

- Pre-Implementation Gate T056 must complete after `/speckit.analyze` and before T001 or any `/speckit.implement` or evaluation action.
- Phase 1 setup precedes all implementation.
- Phase 2 core implementation precedes guardrail completion.
- Guardrails in Phase 3 must wrap model output and CLI actions before provider integration is complete.
- Model integration in Phase 4 supplies clients used by core orchestration and unit tests.
- CLI integration in Phase 5 depends on core, guardrail, and model-service behavior.
- Unit testing in Phase 6 depends on implementation of core and guardrails.
- Final validation in Phase 7 depends on all previous phases.

## Parallel Opportunities

- T003 and T004 can proceed together after T001.
- T033 and T034 can proceed together after provider-selection scaffolding.
- Unit test tasks T043-T054 can be grouped by shared fake clients and guardrail fixtures.
- Ruff and Bandit validation can run independently after implementation.

## Protected-File Boundary

Do not modify `tests/`, `evals/`, `.harness/`, `reference-implementation/`, `thresholds.json`, or `output.schema.json`. Existing protected tests and dataset files may be read and used for validation only.
