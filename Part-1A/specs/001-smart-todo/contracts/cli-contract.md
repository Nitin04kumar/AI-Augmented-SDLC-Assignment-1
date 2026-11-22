# CLI Contract: Smart Todo

## Command Entry

- Runtime command: `python -m todo [--data FILE] <command>`
- Entry-point function: `todo.cli.main(argv: list[str] | None) -> int`
- Default data path: `TODO_DATA_FILE` environment variable or `./tasks.json`

## Valid Commands

### `add TITLE [--priority P] [--tags a,b]`
- Creates a task with a positive ID, trimmed title, default medium priority, default `todo` status, and normalized tags.
- Successful output is a task object.
- Validation errors exit 1.

### `list [--tag T] [--status S] [--sort id|priority]`
- Lists tasks in the required order.
- Successful output is `{"count": n, "tasks": [...]}`.
- Unsupported values exit 1.

### `get ID`
- Returns a task object.
- Unknown ID exits 2.
- Malformed ID exits 1.

### `update ID [--title] [--priority] [--tags]`
- Updates only the supplied fields.
- Empty `--tags` clears tags.
- No fields or invalid values exit 1.
- Unknown ID exits 2.

### `delete ID`
- Deletes a task and returns `{"deleted": id}`.
- Re-deleting an already-deleted task exits 2.

### `status ID NEW_STATUS`
- Changes task status only when the transition is allowed.
- Allowed transitions and invalid transitions follow the exact matrix in the specification.
- Unknown status exits 1.
- Unknown ID exits 2.

## Output Contract

### Success output
All success responses are JSON on stdout.

### Error output
All errors emit JSON to stderr as:
```json
{"error":{"code":"ERROR_CODE","message":"human-readable summary"}}
```

### Exit codes
- `0`: success
- `1`: validation error
- `2`: not found
- `3`: invalid transition
- `4`: storage error

## Storage Contract

- File format:
  ```json
  {"next_id": 3, "tasks": [...]}
  ```
- Task field set: `id`, `title`, `priority`, `tags`, `status`, `created_at`, `updated_at`
- Corrupt or malformed data returns exit 4 and must leave the file unmodified
- Successful writes use temp-file + replace semantics
