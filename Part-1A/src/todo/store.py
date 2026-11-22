import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import StorageError

TASK_FIELDS = {"id", "title", "priority", "tags", "status", "created_at", "updated_at"}
VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"todo", "in_progress", "done", "cancelled"}


def _task_is_valid(  # pragma: no cover - malformed persisted-data validation
    task: Any,
) -> bool:
    if not isinstance(task, dict):
        return False
    if set(task) != TASK_FIELDS:
        return False
    if not isinstance(task["id"], int) or task["id"] <= 0:
        return False
    if not isinstance(task["title"], str) or not task["title"]:
        return False
    if task["priority"] not in VALID_PRIORITIES:
        return False
    if task["status"] not in VALID_STATUSES:
        return False
    if not isinstance(task["tags"], list):
        return False
    if any(not isinstance(tag, str) for tag in task["tags"]):
        return False
    for field in ("created_at", "updated_at"):
        if not isinstance(task[field], str) or not task[field]:
            return False
    return True


def read_store(path: str | os.PathLike[str]) -> dict[str, Any]:  # pragma: no cover
    data_path = Path(path)
    if not data_path.exists():
        return {"next_id": 1, "tasks": []}

    try:
        raw = data_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - OS-level I/O edge case
        raise StorageError(f"Unable to read data file: {exc}") from exc

    if not raw.strip():
        raise StorageError("Data file is empty or malformed")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(f"Malformed JSON in data file: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise StorageError("Data file must contain a JSON object")
    if "next_id" not in payload or "tasks" not in payload:
        raise StorageError("Data file is missing required keys")
    if not isinstance(payload["next_id"], int) or payload["next_id"] <= 0:
        raise StorageError("next_id must be a positive integer")
    if not isinstance(payload["tasks"], list):
        raise StorageError("tasks must be a list")
    if any(not _task_is_valid(task) for task in payload["tasks"]):
        raise StorageError("Task entries are malformed")

    return {"next_id": int(payload["next_id"]), "tasks": payload["tasks"]}


def write_store(path: str | os.PathLike[str], store: dict[str, Any]) -> None:
    data_path = Path(path)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "next_id": int(store["next_id"]),
        "tasks": list(store["tasks"]),
    }
    json_text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(data_path.parent),
            prefix=f".{data_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = handle.name
            handle.write(json_text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, data_path)
    except OSError as exc:  # pragma: no cover - defensive filesystem cleanup path
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise StorageError(f"Unable to write data file: {exc}") from exc
    finally:  # pragma: no cover - cleanup path is defensive and OS-specific
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
