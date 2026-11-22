# Quickstart Validation Guide

## Objective
This guide outlines how to validate the Smart Todo CLI against the specification without modifying the tests or harness. The implementation should be verified only through the project’s existing lint, security, and pytest gates.

## Prerequisites
- Python 3.10+
- Project checkout with `src/`, `tests/`, `.harness/`, and the config files present
- `ruff`, `bandit`, and `pytest-cov` available in the environment

## Validation Flow

### 1. Static validation
```bash
python -m ruff check src tests .harness --config .harness/ruff.toml
python -m bandit -r src -ll
```

**Expected outcome**:
- No lint findings from the project config
- No medium or high severity Bandit findings

### 2. Contract validation
```bash
python -m pytest tests -q --cov=todo --cov-report=term-missing --cov-fail-under=85
```

**Expected outcome**:
- All acceptance tests pass
- Source coverage remains at or above 85%

### 3. Harness validation
```bash
python .harness/run_harness.py --lock
python .harness/run_harness.py --label initial
```

**Expected outcome**:
- Protected-file integrity passes
- Lint gate passes
- Security gate passes
- Test gate passes with coverage threshold satisfied

## Manual CLI checks
These checks validate the command contract without changing the code base:

```bash
python -m todo --data /tmp/tasks.json add "Buy milk"
python -m todo --data /tmp/tasks.json list
python -m todo --data /tmp/tasks.json status 1 done
python -m todo --data /tmp/tasks.json get 1
python -m todo --data /tmp/tasks.json delete 1
```

**Expected outcome**:
- Successful commands emit JSON on stdout
- Errors emit JSON on stderr with the correct error code
- Exit codes match the public contract
- File writes remain atomic and supported by valid state
