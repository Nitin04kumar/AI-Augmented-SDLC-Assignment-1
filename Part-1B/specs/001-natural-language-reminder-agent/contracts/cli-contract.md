# CLI Contract: Natural-Language Reminder Agent

## Command Entry

```text
python -m reminder_agent "<text>" [--now ISO] [--tz TZ] [--existing JSON]
```

Examples:

```bash
python -m reminder_agent "Remind me to call mom tomorrow at 6pm" \
  --now "2026-11-16T09:00:00+05:30" \
  --tz "Asia/Kolkata"

python -m reminder_agent "snooze it for 15 minutes" \
  --now "2026-11-16T09:00:00+05:30" \
  --tz "Asia/Kolkata" \
  --existing '{"id":"r-101","title":"Team standup","remind_at":"2026-11-16T10:00:00+05:30"}'
```

## Core API

```python
parse_request(text, now_iso, tz, existing_reminder, client)
    -> {"output": dict, "raw": str, "actions": list[str]}
```

The model client contract is:

```python
complete(system: str, user: str) -> str
```

## CLI Arguments

| Argument | Required | Behavior |
| --- | --- | --- |
| `text` | Yes | Positional natural-language request |
| `--now` | No | Supplied reference timestamp; must be usable ISO-8601 |
| `--tz` | No | Supplied timezone; default behavior must not silently use an invalid timezone |
| `--existing` | No | Existing reminder JSON context for snooze/reschedule |

For programmatic calls, `now_iso`, `tz`, `existing_reminder`, and `client` are passed explicitly.

## Success Output

For every successfully parsed application request, stdout is exactly one JSON object conforming to the exact fields in `.harness/schema/output.schema.json`.

The only permitted fields are:

```json
{
  "intent": "create",
  "title": "string or null",
  "remind_at": "string or null",
  "recurrence": "daily",
  "needs_clarification": false,
  "missing_fields": [],
  "clarification_question": null,
  "refusal_reason": null,
  "confidence": 0.9
}
```

No indentation or extra stdout text is guaranteed by the contract. Exactly one JSON object must be emitted.

## Reference Time and Timezone Behavior

- If `--now` is omitted, the CLI obtains the current local ISO-8601 timestamp once and passes that timestamp to `parse_request` as `now_iso`.
- The core parser then treats that timestamp as supplied context and does not consult the machine clock for relative-date or snooze arithmetic.
- If `--tz` is omitted or cannot be resolved by `zoneinfo`, no scheduled timestamp is returned. The application returns an OSC-1 clarification instead.
- Explicit `--now` and `--tz` values are preserved; the CLI must not silently replace them.

## Existing Reminder JSON

- If `--existing` is absent, it is passed to the core parser as `null`.
- If `--existing` contains syntactically valid JSON but is structurally unusable as an existing reminder, the CLI may pass it to the core parser for deterministic target validation.
- If `--existing` is malformed JSON, the CLI converts the request to an OSC-1 clarification with `missing_fields=["target_reminder"]`, without modifying reminder state.
- Malformed existing-reminder context must not create, reschedule, or snooze a reminder.

## Output Intent Rules

### `create`

- Non-empty title.
- Valid offset-bearing future `remind_at`.
- Not later than `now` plus five years.

### `reschedule`

- Existing reminder is required.
- Existing reminder title is preserved.
- Valid offset-bearing future `remind_at`.

### `snooze`

- Existing reminder is required.
- Existing title is preserved.
- Time is exactly or semantically `now + requested duration`.

### `clarify`

- `needs_clarification=true`.
- `missing_fields` is non-empty and unique.
- `clarification_question` is non-empty and ends in `?`.
- `remind_at=null`.

### `refuse`

- `refusal_reason` is non-empty.
- `title=null`.
- `remind_at=null`.

## Model-Service Failure Contract

Model and provider failures raise or report `ModelServiceError` separately from OSC-1 application output.

The CLI reports model-service failures on stderr with a safe diagnostic:

```text
model service failure: <safe diagnostic>
```

The CLI writes no success JSON to stdout and exits with status `3`.

The diagnostic must not expose provider secrets or system prompt content.

## Environment Configuration

| Variable | Meaning |
| --- | --- |
| `REMINDER_PROVIDER` | `anthropic`, `openai`, or `mock` |
| `ANTHROPIC_API_KEY` | Anthropic credential |
| `OPENAI_API_KEY` | OpenAI-compatible credential |
| `OPENAI_BASE_URL` | OpenAI-compatible base URL |
| `REMINDER_MODEL` | Provider model name |
| `REMINDER_TEMPERATURE` | Provider temperature |

Secrets may be read only from environment variables. The mock provider is for harness plumbing only.

## In-Scope and Out-of-Scope Actions

In scope:

- Create reminder data
- Reschedule an supplied existing reminder
- Snooze an supplied existing reminder
- Clarify incomplete or unsafe requests
- Refuse unsupported or adversarial requests

Out of scope:

- Sending email
- Deleting reminders
- Persisting reminders
- Delivering notifications
- Searching or selecting reminders independently
- Executing instructions embedded in user text
