# Harness feedback - run 1 (initial)

Fix src/ only. Do NOT edit tests/, specs/, .harness/ or lint/security config.

## Gate: lint - FAIL
Command: `/home/nitin/Downloads/Assignment-1/Part-1A/.venv/bin/python -m ruff check src tests .harness --config .harness/ruff.toml --output-format json`

- {"rule": "I001", "message": "Import block is un-sorted or un-formatted", "file": "tests/conftest.py", "line": 1}

## Gate: tests - FAIL
Command: `/home/nitin/Downloads/Assignment-1/Part-1A/.venv/bin/python -m pytest tests -q --junitxml=/home/nitin/Downloads/Assignment-1/Part-1A/evidence/harness-results/run-001-initial-junit.xml --cov=todo --cov-report=term-missing --cov-fail-under=85`

- {"rule": "gate-failed-without-parsed-issue", "message": "ImportError while loading conftest '/home/nitin/Downloads/Assignment-1/Part-1A/tests/conftest.py'.\ntests/conftest.py:5: in <module>\n    from todo.cli import main\nE   ModuleNotFoundError: No module named 'todo'\n"}

Output tail:
```

```
