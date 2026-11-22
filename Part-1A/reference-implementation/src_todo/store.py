"""JSON persistence with atomic writes (spec FR-08)."""

import json
import os
import tempfile
from pathlib import Path

from todo.errors import StorageError


def _empty() -> dict:
    return {"next_id": 1, "tasks": []}


def load(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return _empty()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StorageError(f"Cannot read data file: {exc}") from exc
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("next_id"), int)
        or not isinstance(data.get("tasks"), list)
    ):
        raise StorageError("Data file has an invalid structure")
    return data


def save(path: str, data: dict) -> None:
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".todo-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, p)
    except OSError as exc:
        raise StorageError(f"Cannot write data file: {exc}") from exc
