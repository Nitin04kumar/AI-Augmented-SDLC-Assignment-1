# Research: Smart Todo CLI

## Decision Record

### Decision: Python 3.10+ standard-library CLI architecture
The implementation will use Python 3.10+ with the standard library only. The CLI will be built around `argparse`, `json`, `pathlib`, `tempfile`, and `os`, matching the project constraints in the constitution and the task seed.

**Rationale**: The seed and constitution explicitly require Python 3.10+, standard-library runtime only, and deterministic behavior. The runtime stack is limited to avoid security issues and to preserve compatibility with the harness.

**Alternatives considered**:
- Add a third-party persistence library or CLI framework: rejected because the seed explicitly forbids non-standard runtime dependencies and the project must remain deterministic and portable.
- Use direct file writes without a temp file: rejected because AC-26 requires atomic writes and AC-25 forbids any partial mutation on failure.

### Decision: Single-package `src/todo` layout
The runtime package will be organized under `src/todo` with separate modules for CLI parsing, domain rules, storage, and exceptions.

**Rationale**: The assignment seed names the intended layout: `src/todo/{cli,service,store,errors}.py` and `__main__.py`. This aligns with the need to separate user input handling from storage and validation logic while keeping the implementation testable.

**Alternatives considered**:
- One large module: rejected because it would mix validation, file I/O, and CLI concerns and increase risk of violating the deterministic and safety constraints.
- Split by command group or feature directories: rejected because the harness and seed expect a compact module layout and the contract tests target the package entry point and exit codes.

### Decision: JSON storage contract and atomic write strategy
State will be stored as a JSON object with the exact top-level keys `next_id` and `tasks` and each task containing exactly `{id, title, priority, tags, status, created_at, updated_at}`.

**Rationale**: The seed explicitly defines the data file format and exact task fields; the tests enforce both structure and file behavior. The atomic write strategy will use a temp file in the same directory and `os.replace()` to preserve file integrity.

**Alternatives considered**:
- Append-only JSON or another serialization format: rejected because the tests require exact top-level schema and persistent state across invocations.
- In-place update of the original file: rejected because it violates the no-partial-write principle in AC-24 and AC-25.

### Decision: Centralized typed errors and exit-code mapping
The implementation will define typed exceptions or equivalent error objects that map directly to contract exit codes: 0 success, 1 validation error, 2 not found, 3 invalid transition, 4 storage error.

**Rationale**: The seed defines the required exit codes and the tests assert exact behavior for argument validation, missing tasks, invalid transitions, corrupted storage, and failed commands.

**Alternatives considered**:
- Return tuples or sentinel values: rejected because it is more error-prone and less explicit than typed exceptions with consistent mapping.
- Different internal codes mapped later: rejected because tests depend on exact public exit codes and JSON error payloads.

## Open Questions Resolved by Contract

- Missing data file semantics: treated as empty state on first write, per the clarification note in the seed.
- Same-state transitions: forbidden, because the specification explicitly lists same-state transitions as invalid, and the tests require the invalid transition code.
- Reopening terminal states: not allowed; `done` and `cancelled` are terminal states under the allowed status transition matrix.
- `--tags ""` behavior: clears the tag list, as required by AC-17.
- Tag case handling: lowercased and deduplicated, preserving first-seen order.

## Verification Strategy

The implementation plan is valid only if it preserves the following gates from the project constitution and harness:

- `ruff check src tests .harness --config .harness/ruff.toml`
- `bandit -r src -ll`
- `pytest tests -q --cov=todo --cov-report=term-missing --cov-fail-under=85`
- harness integrity lock and snapshot flow from `.harness/run_harness.py`

Each design decision above is constrained by one or more acceptance criteria in the specification and is therefore directly testable.
