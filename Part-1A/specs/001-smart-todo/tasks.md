# Tasks: Smart Todo CLI

**Input**: Design documents from `/specs/001-smart-todo/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the code layout and project constraints before implementation.

- [ ] T001 Create the Python package skeleton under `src/todo/` with `__init__.py`, `__main__.py`, `cli.py`, `service.py`, `store.py`, and `errors.py` in accordance with the approved plan and seed requirements. (FR-014; SC-001)
- [ ] T002 [P] Confirm the runtime entry point and module contract in `src/todo/__main__.py` and `src/todo/cli.py` so `python -m todo` and `todo.cli.main(argv: list[str] | None) -> int` are wired correctly before any command logic is implemented. (FR-014; SC-001)
- [ ] T003 [P] Document the implementation guardrails in the working plan: all production changes remain under `src/`, while `tests/`, `.harness/`, `specs/`, and the constitution remain read-only and unchanged. (FR-014; SC-004)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared validation and persistence infrastructure required before US1/US2/US3 can be implemented safely.

- [ ] T004 Implement typed error mapping in `src/todo/errors.py` for exit codes `0`, `1`, `2`, `3`, and `4` and error payloads matching `{"error":{"code":...,"message":...}}` for validation, not-found, invalid-transition, and storage failures. (FR-07, FR-10, FR-12, FR-13, FR-14; AC-15, AC-18, AC-21, AC-22, AC-24, AC-28, AC-29)
- [ ] T005 [P] Implement data-store schema validation and missing-file handling in `src/todo/store.py` so a missing file is treated as empty state on first write and malformed or badly structured JSON raises `STORAGE_ERROR` without modifying the file. (FR-11, FR-12; AC-23, AC-24, AC-25, AC-26)
- [ ] T006 [P] Implement atomic write behavior in `src/todo/store.py` using a temp file in the same directory and `os.replace()` so a failed command leaves the original file byte-identical and no `*.tmp` files remain. (FR-15; AC-25, AC-26)
- [ ] T007 [P] Implement shared task normalization helpers in `src/todo/service.py` for trimming titles, lowercasing and deduplicating tags, validating priorities and statuses, and enforcing the exact allowed field shapes. (FR-01, FR-02, FR-04, FR-05, FR-10; AC-01, AC-02, AC-03, AC-05, AC-06, AC-07, AC-08, AC-17, AC-20, AC-21, AC-22)
- [ ] T008 Implement CLI JSON stdout/stderr contract in `src/todo/cli.py` so successful commands emit a single JSON document to stdout and all error conditions emit structured JSON to stderr with the correct exit code. (FR-13, FR-14; AC-27, AC-28, AC-29)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Task Lifecycle Management (Priority: P1) 🎯 MVP

**Goal**: Create, retrieve, update, and delete tasks with the required validation and deterministic default values.

**Independent Test**: Verify the full add/get/update/delete flow works using the existing contract tests in `tests/test_contract_cli.py` for AC-01 through AC-19.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `add` task creation in `src/todo/service.py` and `src/todo/cli.py` to assign the next ID, default to `medium` priority and `todo` status, trim titles, set empty tags, and reject blank titles and invalid priorities. (FR-01, FR-02, FR-03, FR-04; AC-01, AC-02, AC-03, AC-04, AC-05)
- [ ] T010 [US1] Implement tag normalization and validation for `--tags` in `src/todo/service.py` to lowercase values, trim whitespace, deduplicate in first-seen order, enforce `[a-z0-9_-]{1,20}` and max 10 tags, and treat `--tags ""` as clearing the list. (FR-05, FR-08; AC-06, AC-07, AC-08, AC-17)
- [ ] T011 [US1] Implement `get` and `update` flows in `src/todo/service.py` and `src/todo/cli.py` so IDs must be positive integers, unknown IDs exit `NOT_FOUND`, and updates change only the user-specified fields while leaving other values intact. (FR-07, FR-08; AC-15, AC-16, AC-17, AC-18)
- [ ] T012 [US1] Implement `delete` behavior in `src/todo/service.py` and `src/todo/cli.py` to remove the task, return `{"deleted": id}`, prevent deleted IDs from being reused, and return `NOT_FOUND` on a second delete. (FR-09; AC-04, AC-19)
- [ ] T013 [US1] Validate end-to-end task object shape in the implementation so each task contains exactly `id`, `title`, `priority`, `tags`, `status`, `created_at`, and `updated_at` with no extra keys. (FR-13; AC-27)

**Checkpoint**: At this point, User Story 1 should be fully functional and independently testable.

---

## Phase 4: User Story 2 - Filtering, Sorting, and List Views (Priority: P1)

**Goal**: Support list commands, filtering by tag or status, and deterministic sorting by ID or priority.

**Independent Test**: Verify list/filter/sort behavior using the existing contract tests for AC-09 through AC-14.

### Implementation for User Story 2

- [ ] T014 [US2] Implement `list` command semantics in `src/todo/service.py` and `src/todo/cli.py` so default output is ordered by ascending ID and returns `{"count": n, "tasks": [...]}`. (FR-06; AC-09)
- [ ] T015 [US2] Implement `--tag` filtering in `src/todo/service.py` so tag matching is case-insensitive and returns only tasks carrying the given tag; combine with sort behavior as required. (FR-06; AC-10, AC-13)
- [ ] T016 [US2] Implement `--status` filtering in `src/todo/service.py` so a valid status filter returns only matching tasks and unknown status values exit `VALIDATION_ERROR`. (FR-06; AC-11, AC-14)
- [ ] T017 [US2] Implement priority sorting in `src/todo/service.py` so `--sort priority` orders `high`, `medium`, `low` with ties broken by ascending ID, and ensure tag-filter + sort combinations behave deterministically. (FR-06; AC-12, AC-13)
- [ ] T018 [US2] Enforce invalid sort/filter guardrails in `src/todo/cli.py` and `src/todo/service.py` so unsupported `--sort` or `--status` inputs exit `VALIDATION_ERROR` before any partial success or mutation is produced. (FR-06; AC-14)

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Status Transitions, Persistence, and Contract Safety (Priority: P1)

**Goal**: Enforce valid transitions, preserve data integrity across runs, and maintain a strict CLI contract.

**Independent Test**: Verify the status transition matrix and the persistence/error contract using the existing tests for AC-20 through AC-29.

### Implementation for User Story 3

- [ ] T019 [US3] Implement allowed status-transition validation in `src/todo/service.py` so `todo -> in_progress|cancelled`, `in_progress -> todo|done|cancelled`, and every other transition fails with exit code `3` and leaves the current state unchanged. (FR-10; AC-20, AC-21, AC-22)
- [ ] T020 [US3] Implement `status` command handling in `src/todo/cli.py` so unknown status names exit `VALIDATION_ERROR`, unknown task IDs exit `NOT_FOUND`, and valid transitions return the updated task JSON object. (FR-10, FR-13; AC-20, AC-21, AC-22)
- [ ] T021 [US3] Implement JSON persistence format and write-back logic in `src/todo/store.py` to store `{"next_id": int, "tasks": [...]}` and preserve state across multiple invocations with deterministic ordering and normalized data. (FR-11, FR-15; AC-23, AC-27)
- [ ] T022 [US3] Implement corrupted-storage handling in `src/todo/store.py` so invalid JSON or an incorrectly structured file returns `STORAGE_ERROR`, exit code `4`, and leaves the file byte-identical. (FR-12; AC-24)
- [ ] T023 [US3] Ensure failed commands leave the data file unmodified in `src/todo/service.py` and `src/todo/store.py` for validation errors, invalid transitions, and storage failures, matching the requirement that rejected commands do not mutate the file. (FR-12, FR-15; AC-18, AC-21, AC-24, AC-25)
- [ ] T024 [US3] Verify the module entry point contract in `src/todo/__main__.py` and `src/todo/cli.py` so `python -m todo` behaves identically to the direct CLI process and exits with the correct codes for success and failure paths. (FR-13, FR-14; AC-28, AC-29)

**Checkpoint**: All user stories should now be independently functional and contract-compliant.

---

## Phase 6: Verification, Harness, and Evidence Collection

**Purpose**: Run the project’s required verification gates without modifying protected files and collect evidence of compliance.

- [ ] T025 [P] Run the linter check required by the constitution and harness: `python -m ruff check src tests .harness --config .harness/ruff.toml`. (SC-004; Constitution Quality; harness gate)
- [ ] T026 [P] Run the security scan required by the constitution and harness: `python -m bandit -r src -ll`. (SC-004; Constitution Security; harness gate)
- [ ] T027 [P] Run the contract test suite with coverage: `python -m pytest tests -q --cov=todo --cov-report=term-missing --cov-fail-under=85`. (SC-004; AC-01 through AC-29)
- [ ] T028 [P] Run the harness integrity lock and initial gate pass: `python .harness/run_harness.py --lock` followed by `python .harness/run_harness.py --label initial`. (SC-004; Harness evidence and protected-file validation)
- [ ] T029 [P] Capture the initial generation snapshot required by the project instructions: `python .harness/run_harness.py --snapshot initial` and confirm evidence is stored under `evidence/initial-generation/` without modifying harness or test artifacts. (SC-004; SC-005; Project evidence requirement)
- [ ] T030 Confirm all implementation work remains inside `src/` and no change is made to `tests/`, `.harness/`, `specs/`, or the reference implementation while verification remains green. (FR-014; SC-004; Constitution spec authority and implementation guardrail)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies; can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user story work.
- **Phase 3 (US1)**: Depends on Phase 2.
- **Phase 4 (US2)**: Depends on Phase 2.
- **Phase 5 (US3)**: Depends on Phase 2.
- **Phase 6 (Verification)**: Depends on successful completion of all story work.

### User Story Dependencies

- **US1**: No dependency on other stories; it is the minimum viable task lifecycle.
- **US2**: Depends on foundational validation and the same store contract; can be implemented in parallel with US1 but should be verified against the list/filter/sort contract.
- **US3**: Depends on foundational validation and file-store safety; can be implemented in parallel with US1/US2 once the core contracts are in place.

### Parallel Opportunities

- `T002` and `T003` can run in parallel within Setup.
- `T005`, `T006`, and `T007` can run in parallel within Foundational once the package skeleton exists.
- `T009` through `T013` can be developed as a tight block for US1, with service and CLI logic coordinated around the same validation helpers.
- `T014` through `T018` can be implemented as a list/filter/sort block for US2.
- `T019` through `T024` can be implemented as a persistence/transition block for US3.
- `T025` through `T029` are verification tasks that should run only after the implementation is complete.

---

## Implementation Strategy

- Start with the foundational validation and persistence layer so all later work uses the same rules.
- Implement the core task lifecycle first to satisfy the MVP story and the contract tests.
- Add list/filter/sort logic next to cover ordering and selection semantics.
- Complete status-transition and atomic persistence enforcement last to protect data integrity.
- End with lint, Bandit, pytest coverage, and harness execution to confirm the implementation matches the spec and constitution without weakening any gate.

---

## Verification Checklist for Task Completion

- [ ] Every task has a task ID and file path.
- [ ] All user-story tasks are mapped to the relevant FR/AC IDs in the task description.
- [ ] Setup, foundational, user-story, and verification phases are clearly separated.
- [ ] Atomic-write and failure-preservation verification tasks are included.
- [ ] Lint, Bandit, pytest, coverage, and harness verification tasks are included.
- [ ] No task edits protected harness/spec/test or reference implementation files.
