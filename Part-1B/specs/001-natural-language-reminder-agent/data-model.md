# Data Model: Natural-Language Reminder Agent

## Core Entities

### ReminderRequest

The in-process request context passed to `parse_request`.

| Field | Type | Rules |
| --- | --- | --- |
| `text` | string | <= 500 characters for model calls; blank values become clarification |
| `now_iso` | string | ISO-8601 datetime with timezone offset |
| `tz` | string | IANA timezone name or other valid `zoneinfo` name |
| `existing_reminder` | object or null | Optional target for snooze/reschedule |
| `client` | model client | Must expose `complete(system, user) -> str` |

### ExistingReminder

Optional context supplied to snooze or reschedule operations.

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string/number | Identifies the target; not returned by OSC-1 |
| `title` | string | Preserved for snooze/reschedule where applicable |
| `remind_at` | string | Existing schedule may be supplied for context |

The application does not search, persist, create, or deliver reminder objects. Existing reminder data is parsed only from CLI JSON and passed to the agent.

### ReminderOutput (OSC-1)

The public result object has exactly these fields:

| Field | Type | Rules |
| --- | --- | --- |
| `intent` | enum | `create`, `reschedule`, `snooze`, `clarify`, `refuse` |
| `title` | string/null | <= 100 characters; required and non-empty for create |
| `remind_at` | string/null | Offset-bearing ISO-8601 when an action is scheduled |
| `recurrence` | enum/null | `daily`, `weekly`, `monthly`, or null |
| `needs_clarification` | boolean | True only for clarify |
| `missing_fields` | unique list | Subset of `title`, `date`, `time`, `target_reminder` |
| `clarification_question` | string/null | Required with clarify and must end in `?` |
| `refusal_reason` | string/null | Required for refuse |
| `confidence` | number | Between 0 and 1 inclusive |

No additional fields are permitted.

## Validation and State Rules

### Time validation

- Parse `now_iso` and `remind_at` as ISO-8601 datetimes.
- `remind_at` must carry a timezone offset.
- For `create`, `reschedule`, and `snooze`: `now < remind_at <= now + timedelta(days=1825)`.
- Missing, invalid, offset-less, past, now, or over-horizon times produce clarification.
- Relative expressions resolve against supplied `now` and `tz`.

### Intent rules

| Intent | Required fields | Invariants |
| --- | --- | --- |
| `create` | non-empty title and valid future `remind_at` | INV-02 |
| `reschedule` | existing reminder and valid future `remind_at` | INV-02, INV-06 |
| `snooze` | existing reminder and valid future `remind_at` | INV-02, INV-06 |
| `clarify` | true clarification flag, non-empty missing fields, `?` question, null remind_at | INV-03 |
| `refuse` | refusal reason, null title, null remind_at | INV-05 |

Non-clarify intents require `needs_clarification=false` and `missing_fields=[]` (INV-04).

A model-produced title longer than 100 characters is treated as a clarification rather than returning an invalid scheduled action or a truncated title. The clarification requests a shorter title and leaves `remind_at` null (OSC-1; INV-03).

### Guardrail actions

| ID | Deterministic result |
| --- | --- |
| G-01 | Blank input -> clarify; >500 characters -> refuse; no model call |
| G-02 | Prompt/sentinel leakage -> refuse |
| G-03 | Unsupported or embedded actions -> refuse or ignore; missing target -> clarify |
| G-04 | Invalid or offset-less time -> clarify |
| G-05 | Time <= now or > now+5 years -> clarify |

## Diagnostic Result

`parse_request` returns:

```json
{
  "output": {},
  "raw": "",
  "actions": []
}
```

- `output`: OSC-1 object, or a diagnostic service result only outside normal application parsing.
- `raw`: raw model response when a model call occurred; otherwise an empty string.
- `actions`: deterministic guardrail decisions applied after or before model use.
