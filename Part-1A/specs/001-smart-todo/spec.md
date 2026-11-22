# Feature Specification: Smart Todo CLI

**Feature Branch**: `001-smart-todo`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "Build a deterministic command-line task manager for Smart Todo with JSON-backed persistence, strict validation, atomic writes, and explicit exit-code behavior. The application must support creating, listing, filtering, sorting, retrieving, updating, deleting, and status-transitioning tasks while preserving a stable contract for CLI output, data storage, and error handling."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage tasks from the command line (Priority: P1)

A user wants to add, inspect, update, and remove individual tasks without needing a graphical interface. The CLI must provide a consistent and predictable way to create a task, retrieve it, change details, and delete it when no longer needed.

**Why this priority**: The task lifecycle is the core value of the product. Without reliable add, get, update, and delete flows, the application cannot be used for daily planning.

**Independent Test**: A user can create a task, read it back, update its title or priority, and delete it; the resulting behavior must match the documented contract.

**Acceptance Scenarios**:

1. **Given** a new task list, **When** the user adds a task titled "Buy milk" with no extra options, **Then** a new task is created with the next available ID, default medium priority, default todo status, and empty tags.
2. **Given** an existing task, **When** the user requests the task by ID, **Then** the full task record is returned exactly as stored.
3. **Given** an existing task, **When** the user updates only the supplied fields, **Then** only those fields change and other fields remain unchanged.
4. **Given** an existing task, **When** the user deletes it, **Then** it is removed and a subsequent lookup by that ID fails with the documented not-found result.

---

### User Story 2 - Filter and sort tasks to focus on priorities (Priority: P1)

A user wants to review work in a manageable order by using filters and sort options. The CLI should support narrowing tasks by tags or status and ordering by ID or priority so the user can quickly find the most relevant tasks.

**Why this priority**: Filtering and ordering are essential for task management because lists become hard to use as the backlog grows.

**Independent Test**: A user can list tasks filtered by tag or status, and can sort by priority while preserving a stable tie-break order.

**Acceptance Scenarios**:

1. **Given** several tasks with different priorities and tags, **When** the user lists tasks sorted by priority, **Then** high-priority tasks appear first, medium next, low last, with lower IDs earlier for ties.
2. **Given** tasks tagged with different values, **When** the user filters by a case-insensitive tag, **Then** the returned tasks include only matching tasks.
3. **Given** tasks in different states, **When** the user filters by status, **Then** only tasks in the selected state are included.
4. **Given** a list command with an unknown sort or status option, **When** the user runs it, **Then** the command fails with a validation error and does not produce a partial success result.

---

### User Story 3 - Protect data and ensure predictable behavior (Priority: P1)

A user expects the task database to remain safe even when invalid input or a failed workflow occurs. The CLI must preserve file integrity, reject malformed input consistently, and keep command output deterministic across repeated runs with identical data.

**Why this priority**: Data safety and reproducibility are foundational trust requirements. If a command can corrupt the file or behave inconsistently, the tool cannot be safely used for personal task tracking.

**Independent Test**: A user can invoke the CLI with valid and invalid inputs, corrupt data files, and repeated operations to confirm the file is preserved and the same inputs produce the same results.

**Acceptance Scenarios**:

1. **Given** a valid data file containing tasks, **When** the user runs a command that fails validation or storage checks, **Then** the file remains unchanged.
2. **Given** a corrupted or wrongly structured data file, **When** the user runs any command that reads it, **Then** the CLI reports a storage error and leaves the file untouched.
3. **Given** the same input and task data, **When** the user runs the command twice, **Then** the output stays identical except for timestamps, which are the only expected variation.
4. **Given** a successful write, **When** the command completes, **Then** the data file is updated atomically with no stray temporary files left behind.

---

### Edge Cases

- What happens when a task title is blank, whitespace-only, or longer than 100 characters?
- How does the system handle invalid priorities, malformed IDs, or unknown status names?
- What happens when a transition is illegal, such as moving a task from done to todo or attempting the same status again?
- How should duplicate or mixed-case tags be normalized when they are supplied in a single command?
- What happens when the data file does not yet exist or contains a corrupt JSON payload?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow users to add tasks with a trimmed title, default `medium` priority, default `todo` status, and an empty tag list when no values are supplied.
- **FR-002**: The system MUST reject blank or overlong titles and MUST accept exactly 100-character titles as valid.
- **FR-003**: The system MUST assign a strictly increasing positive integer task ID and MUST never reuse a deleted ID.
- **FR-004**: The system MUST validate `priority` values as `low`, `medium`, or `high` and reject any other value with a validation error.
- **FR-005**: The system MUST normalize tags to lowercase, trim whitespace, remove duplicates in first-seen order, and reject tags that do not match the allowed format or exceed the maximum of 10 tags.
- **FR-006**: The system MUST support listing tasks, filtering by tag or status, and sorting by ID or priority with stable ordering semantics.
- **FR-007**: The system MUST support retrieving a task by ID and MUST fail with a documented not-found result when the task does not exist.
- **FR-008**: The system MUST support updating only the fields explicitly supplied by the user while preserving unchanged values, and MUST treat an empty `--tags` input as clearing the tag list.
- **FR-009**: The system MUST support deleting tasks and MUST prevent deleted IDs from being reused while returning the correct not-found result when deleted again.
- **FR-010**: The system MUST validate and enforce the allowed status transitions: `todo` to `in_progress` or `cancelled`; `in_progress` to `todo`, `done`, or `cancelled`; and MUST reject every other transition with an invalid transition error.
- **FR-011**: The system MUST persist tasks in a JSON structure containing `next_id` and a task list and MUST survive repeated invocations without losing state.
- **FR-012**: The system MUST report malformed or structurally invalid data as a storage error without changing the file contents.
- **FR-013**: The system MUST emit valid JSON on successful stdout output and a structured error object on stderr for validation and runtime failures.
- **FR-014**: The system MUST expose the CLI entry point as `python -m todo` and the function `todo.cli.main(argv: list[str] | None) -> int` with exit codes matching the contract.
- **FR-015**: The system MUST keep output deterministic and file writes atomic so repeated runs with the same input yield consistent results and failed commands do not mutate stored state.

### Key Entities *(include if feature involves data)*

- **Task**: A single to-do item with a unique numeric ID, title, priority, tags, current status, and timestamps for creation and last update.
- **Task List**: The persisted collection of tasks plus the next ID to assign, representing the current application state.
- **Data Store**: The JSON-backed file that stores the task list and ensures atomic write semantics for all changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add, retrieve, update, delete, and transition tasks while following the documented command contract and exit codes.
- **SC-002**: The system accepts all valid task inputs and rejects invalid values with a structured validation error that leaves the underlying data unchanged.
- **SC-003**: The task list remains consistent across repeated invocations, with deterministic ordering and normalized tags.
- **SC-004**: The project maintains at least 85% line coverage in source code and passes the required lint and security checks defined by the governing constitution.
- **SC-005**: Corrupt or malformed data files are reported as storage errors without modifying the original file contents.

## Assumptions

- Users interact with the application through the command line rather than a graphical interface.
- The task data file is stored locally and is treated as a single-user store with no concurrency safeguards beyond atomic writes.
- Missing data files are treated as empty state on first write rather than as a fatal error.
- Status transitions are intentionally limited to the documented allowed paths and are enforced strictly.
- The feature is scoped to the Smart Todo CLI and excludes due dates, multi-user workflows, UI layers, and networked integrations.
