<!-- Sync Impact Report: Version change: initial -> 1.0.0; Modified principles: created the Smart Todo constitution from the Part-1A governance template; Added sections: Quality, Security, Testing, Spec Authority, Determinism, Data Safety, Stack, Product Constraints, Review Workflow; Removed sections: none; Deferred items: none -->
# Smart Todo & Task Management Constitution

## Core Principles

### I. Quality and Lint Integrity
The Smart Todo application MUST keep the codebase clean and reviewable. The project MUST pass `ruff check` with the repository configuration in `.harness/ruff.toml` for `src/`, `tests/`, and `.harness/` without any reported issues. Lint violations are not treated as acceptable debt and must be resolved before release or acceptance.

### II. Security and Trust Boundaries
The application MUST enforce strict security constraints. It MUST NOT use `eval`, `exec`, `pickle`, `shell=True`, `os.system`, hard-coded secrets, or any network access in the application code. `bandit -r src -ll` MUST report zero high or medium severity findings, and any security regression is an automatic blocker.

### III. Testing as the Source of Truth
Every acceptance criterion for the Smart Todo CLI MUST have at least one binary pytest test. Coverage for `src/` MUST remain at or above 85%, and the test suite MUST validate behavior before implementation is accepted. The project MUST prefer adding explicit tests over implicit assumptions; no individual criterion may be left untested.

### IV. Spec Authority and Controlled Change
The specification, acceptance criteria, and harness outputs are the authoritative contract for this project. The coding agent MUST NOT edit `tests/`, `.harness/`, `specs/`, or the constitution itself, and MUST NOT delete, skip, weaken, or disable tests, lint rules, or security rules. Any approved change to the product contract MUST occur only through Spec Kit artifacts with traceable change history; implementation MUST remain constrained by the authoritative specification.

### V. Determinism and Reproducibility
The CLI MUST be deterministic. Given the same inputs and the same data file content, it MUST produce the same observable output except for timestamp fields, which may vary only when the system legitimately records time. The project MUST avoid nondeterministic ordering, hidden state, time-based branching, or environment-dependent behavior that changes output under equivalent conditions.

### VI. Safety of Data and Atomic Writes
The application MUST preserve user data safely. All writes to the task data file MUST be atomic by using a temporary file and replacement operation; a failed command MUST leave the existing data file byte-identical. The CLI MUST reject corrupt or malformed data with a storage error and MUST NOT modify the file during a failed operation.

### VII. Stack and Standard Library Discipline
The application MUST target Python 3.10 or newer and MUST use only the Python standard library for runtime behavior. The project MUST avoid adding third-party application dependencies unless a governing specification explicitly authorizes them. This keeps the application portable, deterministic, and compatible with the enforced security and lint rules.

## Product and Application Constraints

The project implements a deterministic single-user command-line task manager for Smart Todo. The application entry point MUST be `python -m todo`, with `todo.cli.main(argv: list[str] | None) -> int` exposing the process exit code contract. All successful command results MUST emit a single JSON document on stdout; all error paths MUST emit `{"error":{"code":...,"message":...}}` to stderr.

The data model MUST remain a JSON-backed task store with exactly the required fields: `id`, `title`, `priority`, `tags`, `status`, `created_at`, and `updated_at`. The CLI MUST honor the specified exit codes for validation errors, not-found conditions, invalid transitions, and storage failures. Task IDs MUST be positive integers, tag normalization MUST be deterministic, and invalid transitions MUST never mutate the stored state.

The project scope is intentionally narrow: no due dates, multi-user behavior, network access, user accounts, or UI layer are in scope. The use of the environment variable `TODO_DATA_FILE` or the default path `./tasks.json` MUST remain consistent with the specification, and the contract for command behavior, storage, and error reporting is authoritative over any implementation convenience.

## Development Workflow and Review Gates

All work on the Smart Todo application MUST be implemented only under `src/`. `tests/`, `.harness/`, `specs/`, and `.specify/` are read-only and MUST NOT be edited, deleted, weakened, or bypassed during implementation. The harness and test files are frozen artifacts that define the approved contract and must remain as recorded evidence of compliance.

Before acceptance, the implementation MUST run the project checks required by the specification: lint, security scanning, and pytest with the acceptance criteria. No implementation path may rely on weakening the harness, skipping verification, or modifying recorded results. If the project changes its external contract, the change MUST be propagated through Spec Kit artifacts and the stored harness evidence.

## Governance

This constitution supersedes informal project habits and governs the Smart Todo task manager during Part 1A and any subsequent amendments. Any change to the governing principles, required checks, or product constraints MUST be recorded as a Spec Kit amendment and MUST include a clear rationale, the version bump, and the impact on compliance expectations.

The project MUST review compliance with this constitution at every material change to the CLI contract, the data model, or the validation rules. A change is non-compliant if it weakens the enforced lint, security, testing, determinism, or data-safety guarantees. All amended governance must preserve the requirement that implementation evidence be reproducible and auditable.

**Version**: 1.0.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15
