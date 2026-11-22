# Part 1A - Spec Kit prompt pack (Smart Todo & Task CLI)

Paste each block into the matching command in your coding agent (Claude Code / Copilot / etc.) inside the
`Part-1A/` folder after `specify init`. **Read and edit every output before approving it** - the specs must
be yours. The pre-built `tests/` assume exactly the contract below; if you change the contract, change the
spec through Spec Kit, then update tests/lock and record the change in harness-log.md.

---
## 1. /speckit.constitution
```
Create a constitution for a small deterministic Python CLI application with these measurable principles:
1. Quality: `ruff check` (config .harness/ruff.toml) must report zero issues on src/, tests/, .harness/.
2. Security: `bandit -r src -ll` must report zero medium/high findings. No eval/exec, pickle, shell=True,
   os.system, hard-coded secrets, or network access in the application.
3. Testing: every acceptance criterion has at least one binary pytest test; line coverage of src >= 85%.
4. Spec authority: tests and acceptance criteria are derived from the specification. The coding agent MUST NOT
   edit tests/, .harness/, specs/ or the constitution, delete/skip/weaken tests, disable lint/security rules,
   or edit recorded harness results. Spec changes happen only via Spec Kit artifacts with change history.
5. Determinism: identical inputs and identical data file give identical outputs (except timestamps).
6. Safety of data: writes are atomic; a failed command never modifies the data file.
7. Stack: Python >= 3.10, standard library only for the application.
```

## 2. /speckit.specify
```
Build "Smart Todo", a deterministic command-line task manager: `python -m todo [--data FILE] <command>`.
Data file default: env TODO_DATA_FILE or ./tasks.json. All success output is one JSON document on stdout;
all errors are JSON {"error":{"code":...,"message":...}} on stderr. Entry point must also expose
`todo.cli.main(argv: list[str] | None) -> int` returning the process exit code.

Task object fields (exactly): id, title, priority, tags, status, created_at, updated_at.
Exit codes: 0 ok; 1 VALIDATION_ERROR; 2 NOT_FOUND; 3 INVALID_TRANSITION; 4 STORAGE_ERROR.

Commands: add TITLE [--priority P] [--tags a,b]; list [--tag T] [--status S] [--sort id|priority];
get ID; update ID [--title] [--priority] [--tags]; delete ID; status ID NEW_STATUS.
list prints {"count": n, "tasks": [...]}; delete prints {"deleted": id}.

Functional requirements and binary acceptance criteria:
FR-01 Add: AC-01 first task gets id 1, priority medium, status todo, tags []. AC-02 title trimmed.
  AC-03 title blank or >100 chars -> exit 1 (exactly 100 accepted). AC-04 ids increase and a deleted id is
  never reused. AC-05 priority must be low|medium|high else exit 1.
FR-02 Tags: AC-06 lower-cased, trimmed, de-duplicated, first-seen order kept. AC-07 each tag must match
  [a-z0-9_-]{1,20} else exit 1. AC-08 max 10 tags (11 -> exit 1).
FR-03 List/filter: AC-09 default order by id asc. AC-10 --tag filter (case-insensitive). AC-11 --status filter.
  AC-14 unknown --sort/--status value -> exit 1.
FR-04 Priority sort: AC-12 --sort priority = high, medium, low; ties by id asc. AC-13 tag filter + sort combine.
FR-05 Get/Update: AC-15 get returns task; unknown id -> exit 2. AC-16 id must be a positive integer else exit 1.
  AC-17 update changes only supplied fields; --tags replaces the tag list ("" clears it).
  AC-18 update with no fields or any invalid value -> exit 1 and task unchanged; unknown id -> exit 2.
FR-06 Delete: AC-19 delete removes; deleting again -> exit 2.
FR-07 Status transitions: allowed todo->in_progress, todo->cancelled, in_progress->todo, in_progress->done,
  in_progress->cancelled. AC-20 allowed transitions succeed. AC-21 every other transition (including same-state,
  and anything out of done/cancelled) -> exit 3, status unchanged. AC-22 unknown status name -> exit 1.
FR-08 Persistence: AC-23 state stored as JSON {"next_id":int,"tasks":[...]} and survives invocations.
  AC-24 corrupt or wrongly-structured file -> exit 4 and file untouched. AC-25 any rejected command leaves the
  file byte-identical. AC-26 writes are atomic (temp file + rename), no *.tmp left behind.
FR-09 Contract: AC-27 task JSON has exactly the 7 fields. AC-28 argument errors -> JSON on stderr, exit 1.
  AC-29 `python -m todo` behaves identically as a subprocess.
Non-functional: NFR-01 lint clean. NFR-02 bandit clean. NFR-03 coverage >= 85%.
Out of scope: due dates, multi-user, network/API, UI.
```

## 3. /speckit.clarify
Answer what the agent asks; if it asks nothing, deliberately probe these and record the decisions:
same-state transitions; whether done tasks can be reopened (decision: no, terminal); how `--tags ""` behaves;
tag case handling; what happens when the data file is missing (decision: treated as empty, created on first write).

## 4. /speckit.plan
```
Python 3.10+, standard library only (argparse, json, pathlib, tempfile, os). Layout: src/todo/{cli,service,store,errors}.py
+ __main__.py. Pure business rules in service.py, I/O in store.py (atomic write via tempfile + os.replace),
argument parsing/printing in cli.py, typed exceptions carrying exit codes in errors.py.
Tests already exist in tests/ (pytest) and the harness in .harness/ - do not plan to modify them.
```

## 5. /speckit.tasks
Accept the generated list but make sure each task cites FR/AC ids (add them if missing), and that
"implement src only; tests/.harness are read-only" appears as a constraint.

## 6. /speckit.analyze
Run it and keep the report. Fix real inconsistencies in the upstream artifact (not in code) and record the change.

## 7. Before /speckit.implement
1. Make sure tests/ and .harness/ are in place, then freeze them: `python .harness/run_harness.py --lock`.
2. Start `/speckit.implement` with this addition:
```
Implement ONLY under src/. tests/, .harness/, specs/ and .specify/ are read-only for you. Do not skip, delete or
weaken tests, do not change lint/security configuration, do not touch evidence/. Run nothing that edits harness
results. When finished, stop; the human will run the harness.
```
3. Immediately: `python .harness/run_harness.py --snapshot initial` (preserves first generation), then
   `python .harness/run_harness.py --label initial`.
