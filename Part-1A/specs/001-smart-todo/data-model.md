# Data Model: Smart Todo CLI

## Core Entities

### Task
A `Task` is the primary persisted object used by the CLI.

| Field | Type | Rules |
| --- | --- | --- |
| `id` | integer | Positive integer, unique, never reused after deletion |
| `title` | string | Trimmed, non-empty, <= 100 characters |
| `priority` | string | One of `low`, `medium`, `high` |
| `tags` | list[str] | Lowercase, trimmed, deduplicated, max 10 items |
| `status` | string | One of `todo`, `in_progress`, `done`, `cancelled` |
| `created_at` | string | ISO-like timestamp emitted by the runtime |
| `updated_at` | string | ISO-like timestamp updated on each write |

### Task Store
The persistent state is a JSON object with the following top-level shape:

```json
{
  "next_id": 3,
  "tasks": [
    {
      "id": 1,
      "title": "Buy milk",
      "priority": "medium",
      "tags": ["home"],
      "status": "todo",
      "created_at": "2026-11-15T12:00:00Z",
      "updated_at": "2026-11-15T12:00:00Z"
    }
  ]
}
```

Rules:
- `next_id` is the next positive integer to assign after the highest task ID in the store.
- `tasks` is a list of task objects in insertion order or ID order as required by command semantics.
- The file is read-only until a successful write transaction completes.
- A malformed or structurally incorrect data file triggers storage error handling and leaves the file untouched.

## Validation Rules

### Title validation
- Must be trimmed before storage.
- Must not be empty or all whitespace.
- Must be <= 100 characters.
- Exact length 100 is valid.

### Priority validation
- Allowed values: `low`, `medium`, `high`.
- Case-sensitive in the specification contract unless parsed through normalized CLI arguments.

### Tag validation
- Input is split on commas and normalized by trimming whitespace.
- Tags are lowercased, deduplicated in first-seen order, and validated against `[a-z0-9_-]{1,20}`.
- Max 10 tags.
- Empty `--tags ""` clears the tag list.

### Status validation
- Allowed values: `todo`, `in_progress`, `done`, `cancelled`.
- Transition matrix is restricted to the authorized paths defined by the seed.

## State Transitions

| From | To | Allowed |
| --- | --- | --- |
| `todo` | `in_progress` | Yes |
| `todo` | `cancelled` | Yes |
| `in_progress` | `todo` | Yes |
| `in_progress` | `done` | Yes |
| `in_progress` | `cancelled` | Yes |
| `todo` | `todo` | No |
| `todo` | `done` | No |
| `in_progress` | `in_progress` | No |
| `done` | `todo` | No |
| `done` | `in_progress` | No |
| `done` | `cancelled` | No |
| `cancelled` | `todo` | No |
| `cancelled` | `done` | No |

## Persistence and Storage Semantics

- Reads must validate the storage schema before use.
- A corrupt JSON document or wrong schema yields a storage error.
- Successful writes use a temp file in the same directory and replace the target file atomically.
- Failed commands never modify the original data file byte-for-byte.
- No temporary file must remain after command completion.

## CLI Output Contract

### Success payload shapes
- `add`, `get`, `update`, `status`: JSON task object
- `list`: `{"count": n, "tasks": [...]}`
- `delete`: `{"deleted": id}`

### Error payload shape
```json
{"error":{"code":"VALIDATION_ERROR","message":"..."}}
```

The code must match the contract:
- 0 = OK
- 1 = VALIDATION_ERROR
- 2 = NOT_FOUND
- 3 = INVALID_TRANSITION
- 4 = STORAGE_ERROR
