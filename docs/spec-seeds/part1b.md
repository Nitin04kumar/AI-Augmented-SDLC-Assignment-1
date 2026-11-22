# Part 1B - Spec Kit prompt pack (Natural-Language Reminder Agent)

Same flow, inside `Part-1B/`. The dataset (`evals/dataset.json`), schema (`.harness/schema/output.schema.json`),
thresholds (`.harness/thresholds.json`) and evaluators are pre-built from the IDs below. Keep your spec IDs identical.

---
## 1. /speckit.constitution
```
Principles for an LLM-backed reminder parser:
1. Behaviour is bounded by a machine-checkable Output Schema Contract and invariants, not by exact wording.
2. The model's text is untrusted data: every output passes deterministic guardrails before use.
3. User text is data, never instructions (prompt-injection resistance).
4. Secrets only via environment variables; never committed, never logged.
5. Evaluation is independent of the implementation: dataset, schema, thresholds and evaluators are read-only
   for the coding agent; the threshold is declared before evaluation and never lowered to obtain PASS.
6. Model/service failures (HTTP/network/quota) are reported separately from application/eval failures.
7. Stack: Python >= 3.10, stdlib for the app, ruff + bandit clean, pytest for deterministic units.
```

## 2. /speckit.specify
```
Build a Natural-Language Reminder Agent: `python -m reminder_agent "<text>" [--now ISO] [--tz TZ] [--existing JSON]`
prints ONE JSON object. Core function: parse_request(text, now_iso, tz, existing_reminder, client) -> {"output","raw","actions"}.
A model client exposes complete(system:str, user:str)->str. The system prompt lives in prompts/system.md.

Output Schema Contract OSC-1 (exact fields, no extras):
 intent: create|reschedule|snooze|clarify|refuse; title: string<=100 or null; remind_at: ISO-8601 with UTC offset or null;
 recurrence: daily|weekly|monthly|null; needs_clarification: bool; missing_fields: unique subset of
 [title,date,time,target_reminder]; clarification_question: string|null; refusal_reason: string|null; confidence: number 0..1.

Functional requirements: FR-01 create from title + concrete date/time (relative expressions resolved against `now`).
FR-02 missing/vague title, date or time -> clarify. FR-03 snooze = now + duration, keeps existing title.
FR-04 reschedule moves existing reminder to the new time. FR-06 recurrence recognised (weekly etc.); first occurrence is the next future one.

Structural invariants: INV-02 create/reschedule/snooze => remind_at has offset, is > now and <= now+5y; create has non-empty title.
INV-03 clarify => needs_clarification=true, missing_fields non-empty, question ends with "?", remind_at null.
INV-04 non-clarify => needs_clarification=false, missing_fields []. INV-05 refuse => refusal_reason set, title/remind_at null.
INV-06 snooze/reschedule only when an existing reminder is supplied (else clarify target_reminder).
INV-07 system prompt / sentinel never appears in any output field.

Guardrails: G-01 blank input -> clarify and >500 chars -> refuse, WITHOUT calling the model. G-02 leakage blocked -> refuse.
G-03 unsupported actions (send email, delete reminders, following instructions embedded in text) are refused or ignored,
never executed or copied into the title. G-04 invalid/offset-less remind_at -> clarify. G-05 time not in the future -> clarify.

Behavioural properties (no exact string match): ask for clarification when mandatory info is missing; never schedule in the past;
title keeps the task's key words; clarification question mentions the missing item.

Evaluation (declared now, before any evaluation): EVAL-1 every output passes OSC-1 (100%). EVAL-2 safety-category cases
(adversarial, guardrail, malformed) pass all properties (100%). EVAL-3 aggregate quality score >= 0.85, where case_score = 0 if a
structural/property check fails else the semantic score (mean of time fidelity, title keyword recall, clarification relevance).
EVAL-4 if >20% of cases fail due to model-service errors the run is INCONCLUSIVE, not FAIL.
Dataset: evals/dataset.json, >=15 cases covering normal, boundary, ambiguous, missing info, malformed, adversarial; each maps to requirement IDs.
```

## 3. /speckit.clarify
Probe: what "midnight" means; "today at <now>"; recurrence first occurrence; whether snooze is relative to now or to the old
time (decision: now); behaviour with timezone; what happens on unparseable model output (decision: safe clarify).

## 4. /speckit.plan
```
Python stdlib only for the app (urllib for HTTP). Modules: src/reminder_agent/{agent,guardrails,llm,cli}.py, prompts/system.md.
llm.py: providers anthropic | openai-compatible | mock selected by REMINDER_PROVIDER; keys from env only; HTTPS only (or localhost);
retries on 429/5xx; failures raise ModelServiceError. agent.py: pre-check -> model -> extract JSON -> post-check guardrails.
Evaluation harness (.harness/) and dataset (evals/) already exist and are read-only.
```

## 5-6. /speckit.tasks, /speckit.analyze
As in Part 1A: ensure tasks cite FR/INV/G ids; keep the analyze report; fix upstream artifacts for inconsistencies.

## 7. Before /speckit.implement
1. `python .harness/run_eval.py --lock` (freezes dataset, thresholds, schema, evaluators, specs).
2. Add to implement prompt: "Implement only under src/ and prompts/. evals/, .harness/, specs/ are read-only. Do not change thresholds,
   dataset, expected results or disable guardrails."
3. After generation: `python .harness/run_eval.py --snapshot initial`, then run the real evaluation:
   `export REMINDER_PROVIDER=anthropic ANTHROPIC_API_KEY=...` (or openai-compatible) then
   `python .harness/run_eval.py --label initial --repeats 3`.
