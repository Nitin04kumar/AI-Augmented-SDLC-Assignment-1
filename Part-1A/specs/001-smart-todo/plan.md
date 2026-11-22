# Implementation Plan: Smart Todo CLI

**Branch**: `001-smart-todo` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from [spec.md](./spec.md)

## Summary

The Smart Todo CLI is a deterministic single-user Python task manager that persists task state to a JSON file and exposes a strict JSON command-line contract. The implementation will keep the logic in `src/todo` with separate modules for CLI parsing, validation and business rules, storage, and typed error handling. The plan preserves the constraints from the constitution and the Part-1A seed: Python 3.10+ only, no non-standard runtime dependencies, no weakening of tests or harness, atomic writes, deterministic output, and strict exit-code behavior.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Standard library only (`argparse`, `json`, `pathlib`, `tempfile`, `os`, `re`, `dataclasses` if useful)

**Storage**: JSON file with `next_id` and `tasks` persisted locally; writes use temp-file + rename semantics

**Testing**: `pytest` with coverage threshold enforced through the harness and contract tests in `tests/`

**Target Platform**: Linux CLI environment for the assignment harness

**Project Type**: deterministic CLI application

**Performance Goals**: no explicit throughput target; behavioral correctness and deterministic output are higher priority than performance

**Constraints**: strict lint/security gates, requirement to never touch tests/harness/spec files, file atomicity, deterministic formatting, no third-party runtime dependencies, and stable JSON output only

**Scale/Scope**: single-user Todo list with bounded task set, no network or UI features, no out-of-scope extras

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The plan conforms to the constitution because it preserves all governing requirements:

- Quality: planned validation includes `ruff check` using `.harness/ruff.toml`.
- Security: design prohibits `eval`, `exec`, `pickle`, `shell=True`, `os.system`, hard-coded secrets, and network access.
- Testing: every acceptance criterion has a corresponding contract test in `tests/`; coverage target remains >= 85%.
- Spec authority: implementation work is scoped to `src/` only; tests, harness, specs, and constitution remain read-only.
- Determinism: all command output and ordering rules are defined and repeatable.
- Safety: atomic write strategy and no-modify-on-failure rules are explicit.
- Stack: runtime remains Python 3.10+ standard library only.

No unresolved constitution violations are identified in this plan.

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-todo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md  # generated in a later phase, not part of this plan
```

### Source Code (repository root)

```text
src/
├── todo/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── service.py
│   ├── store.py
│   ├── errors.py
│   └── models.py   # optional if the implementation prefers a small data container
└── ...
```

**Structure Decision**: The repository will follow the seed's recommended layout for a compact command-line package: `src/todo` with one module each for CLI parsing, domain/service logic, persistence, and typed errors. No extra packages are needed because the feature is small, deterministic, and contract-driven.

## Architecture

### 1. CLI layer (`src/todo/cli.py`)
Responsibilities:
- Parse CLI arguments with `argparse`.
- Validate command names and their argument combinations.
- Resolve the data file path from `--data` or `TODO_DATA_FILE` or the default `./tasks.json`.
- Translate CLI errors into JSON error payloads on stderr and the correct exit code.
- Call service logic for `add`, `list`, `get`, `update`, `delete`, `status` commands.
- Serialize successful results as JSON to stdout.

Key invariants:
- All successful outputs are valid JSON objects.
- All errors are written as `{"error":{"code":...,"message":...}}` to stderr.
- Unknown command paths must exit 1 with a validation error.

### 2. Service layer (`src/todo/service.py`)
Responsibilities:
- Enforce business rules and validation.
- Normalize titles, priorities, tags, and status values.
- Enforce status transition rules and ID semantics.
- Enforce per-command filtering, sorting, and list semantics.
- Coordinate read/write operations against the store.

Key invariants:
- A rejected command never mutates task state.
- The service is pure with respect to its input state to the extent possible.
- Validation logic is centralized to minimize duplication and preserve deterministic behavior.

### 3. Storage layer (`src/todo/store.py`)
Responsibilities:
- Read and validate the JSON task file.
- Return typed storage errors for corrupt or malformed files.
- Serialize the in-memory state back to JSON using atomic writes.
- Use a temp file in the same directory and `os.replace()`.

Key invariants:
- The original file remains byte-identical on any rejected or failed command.
- No `*.tmp` files remain after writes complete.
- A structurally invalid file is rejected before any state mutation occurs.

### 4. Error layer (`src/todo/errors.py`)
Responsibilities:
- Define typed exceptions or equivalent error objects for validation, not-found, invalid transition, and storage failures.
- Map errors to the exact public exit codes and JSON payloads.

Key invariants:
- The public API uses exact exit codes required by the seed.
- All errors are human-readable and consistent with contract tests.

### 5. Module entry point (`src/todo/__main__.py`)
Responsibilities:
- Allow `python -m todo` execution.
- Invoke the CLI main function and return its exit code.

## Data Flow

1. CLI receives arguments and resolves the data file path.
2. CLI validates the command shape and delegates to the service.
3. Service reads the current task store via the storage layer.
4. Service validates input fields, transition rules, and sort/filter options.
5. If validation fails, the service raises a typed error without mutating the file.
6. If validation succeeds, service updates the in-memory task list and timestamp fields.
7. Storage layer writes a new JSON document atomically.
8. CLI prints either a JSON task payload or the correct JSON error object.

## Storage Design

### File format
The persisted state is a single JSON document:

```json
{"next_id": 3, "tasks": [...]}
```

Each task uses exactly these fields in this order or equivalent logical structure:
`id`, `title`, `priority`, `tags`, `status`, `created_at`, `updated_at`.

### Read-path contract
- If the file does not exist, treat it as empty state when creating a new entry.
- If the file exists but is invalid JSON or wrong structure, return a storage error and do not modify the file.
- The implementation must not silently repair corrupted state.

### Write-path contract
- Write to a temp file in the same directory.
- Ensure the temp file is fully written and flushed.
- Replace the target file with `os.replace()`.
- Clean up no longer-needed temp files before completion.

## Validation Strategy

### Input/field validation
- Title: trimmed and must be non-empty and <= 100 characters
- Priority: one of `low`, `medium`, `high`
- Tags: lowercased, trimmed, deduplicated, max 10, regex-safe tokens
- ID: positive integer only
- Status: one of `todo`, `in_progress`, `done`, `cancelled`

### Semantic validation
- Reject invalid transitions before writing
- Reject unknown filter values and sort keys
- Reject updates with no actual field changes or invalid field values
- Reject duplicate or malformed tag input before state mutation

## Error Handling and Exit Codes

| Exit code | Meaning | Typical triggers |
| --- | --- | --- |
| 0 | success | valid command completed |
| 1 | `VALIDATION_ERROR` | bad arguments, invalid title/priority/tags/id/status/filter/sort |
| 2 | `NOT_FOUND` | unknown item ID |
| 3 | `INVALID_TRANSITION` | forbidden state change |
| 4 | `STORAGE_ERROR` | corrupted file, bad JSON, invalid schema |

These values must align exactly with the tests and the assignment contract.

## Lint, Security, and Test Verification

The implementation phase must validate the application with the repository harness and project configuration:

- `python -m ruff check src tests .harness --config .harness/ruff.toml`
- `python -m bandit -r src -ll`
- `python -m pytest tests -q --cov=todo --cov-report=term-missing --cov-fail-under=85`
- `python .harness/run_harness.py --lock` and `python .harness/run_harness.py --label initial`

The project contract prohibits modifying the harness or tests. Any failure in these gates reflects either a real implementation bug or a contract violation and must be fixed in `src` only.

## Risk Considerations

- Output format drift: all successful commands must emit a JSON document consistent with the contract.
- File corruption: invalid storage state must never be silently repaired.
- Invalid transitions: same-state and terminal-state transitions must be rejected even when legacy records exist.
- Tag handling: ordering and normalization must be deterministic under repeated runs.
- Hidden nondeterminism: avoid relying on unsorted iteration when output order is expected.

## Done When

- The structure above is implemented under `src/todo` only.
- Every acceptance criterion from the spec is satisfied.
- The linter, security scan, and pytest coverage gates pass.
- The harness passes without modification to protected files.
