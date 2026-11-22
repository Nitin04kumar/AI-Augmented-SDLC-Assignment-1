import re
from datetime import datetime, timezone
from typing import Any

from .errors import InvalidTransitionError, NotFoundError, ValidationError

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"todo", "in_progress", "done", "cancelled"}
STATUS_TRANSITIONS = {
    "todo": {"in_progress", "cancelled"},
    "in_progress": {"todo", "done", "cancelled"},
    "done": set(),
    "cancelled": set(),
}
TAG_PATTERN = re.compile(r"^[a-z0-9_-]{1,20}$")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_title(value: str | None) -> str:
    if not isinstance(value, str):
        raise ValidationError("Title must be a string")
    title = value.strip()
    if not title:
        raise ValidationError("Title cannot be blank")
    if len(title) > 100:
        raise ValidationError("Title must be 100 characters or fewer")
    return title


def normalize_priority(value: str | None, default: str = "medium") -> str:
    if value is None:
        return default
    if value not in VALID_PRIORITIES:
        raise ValidationError("Priority must be one of: low, medium, high")
    return value


def normalize_status(value: str | None) -> str:
    if value is None:
        raise ValidationError("Status is required")
    if value not in VALID_STATUSES:
        raise ValidationError("Status must be one of: todo, in_progress, done, cancelled")
    return value


def normalize_id(value: Any) -> int:
    if isinstance(value, bool):
        raise ValidationError("ID must be a positive integer")
    if isinstance(value, int):
        task_id = value
    else:
        text = str(value)
        if not re.fullmatch(r"\d+", text):
            raise ValidationError("ID must be a positive integer")
        task_id = int(text)
    if task_id <= 0:
        raise ValidationError("ID must be a positive integer")
    return task_id


def normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if value == "":
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raise ValidationError("Tags must be a comma-separated string or list")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        token = str(item).strip().lower()
        if token == "":
            continue
        if not TAG_PATTERN.fullmatch(token):
            raise ValidationError("Each tag must match [a-z0-9_-]{1,20}")
        if token in seen:
            continue
        seen.add(token)
        normalized.append(token)
        if len(normalized) > 10:
            raise ValidationError("A task can have at most 10 tags")
    return normalized


def _task_lookup(store: dict[str, Any], task_id: int) -> dict[str, Any]:
    for task in store["tasks"]:
        if task["id"] == task_id:
            return task
    raise NotFoundError(task_id)


def add_task(
    store: dict[str, Any],
    title: str,
    priority: str | None = None,
    tags: Any = None,
) -> dict[str, Any]:
    normalized_title = normalize_title(title)
    normalized_priority = normalize_priority(priority, default="medium")
    normalized_tags = normalize_tags(tags if tags is not None else [])
    timestamp = now_iso()
    task = {
        "id": int(store["next_id"]),
        "title": normalized_title,
        "priority": normalized_priority,
        "tags": normalized_tags,
        "status": "todo",
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    store["tasks"].append(task)
    store["next_id"] = int(store["next_id"]) + 1
    return task


def list_tasks(
    store: dict[str, Any],
    *,
    tag: str | None = None,
    status: str | None = None,
    sort: str = "id",
) -> dict[str, Any]:
    tasks = list(store["tasks"])
    if tag is not None:
        target = str(tag).strip().lower()
        tasks = [task for task in tasks if target in {t.lower() for t in task["tags"]}]
    if status is not None:
        selected = normalize_status(status)
        tasks = [task for task in tasks if task["status"] == selected]
    if sort == "id":
        tasks.sort(key=lambda task: task["id"])
    elif sort == "priority":
        rank = {"high": 0, "medium": 1, "low": 2}
        tasks.sort(key=lambda task: (rank[task["priority"]], task["id"]))
    else:
        raise ValidationError("Sort must be one of: id, priority")
    return {"count": len(tasks), "tasks": tasks}


def get_task(store: dict[str, Any], task_id: Any) -> dict[str, Any]:
    found_id = normalize_id(task_id)
    return _task_lookup(store, found_id)


def update_task(
    store: dict[str, Any],
    task_id: Any,
    *,
    title: str | None = None,
    priority: str | None = None,
    tags: Any = None,
) -> dict[str, Any]:
    found_id = normalize_id(task_id)
    task = _task_lookup(store, found_id)
    if title is None and priority is None and tags is None:
        raise ValidationError("At least one field must be supplied for update")

    if title is not None:
        task["title"] = normalize_title(title)
    if priority is not None:
        task["priority"] = normalize_priority(priority)
    if tags is not None:
        task["tags"] = normalize_tags(tags)

    task["updated_at"] = now_iso()
    return task


def delete_task(store: dict[str, Any], task_id: Any) -> dict[str, Any]:
    found_id = normalize_id(task_id)
    _task_lookup(store, found_id)
    store["tasks"] = [item for item in store["tasks"] if item["id"] != found_id]
    return {"deleted": found_id}


def change_status(store: dict[str, Any], task_id: Any, status: str) -> dict[str, Any]:
    found_id = normalize_id(task_id)
    task = _task_lookup(store, found_id)
    next_status = normalize_status(status)
    current_status = task["status"]
    if next_status == current_status:
        raise InvalidTransitionError(current_status, next_status)
    if next_status not in STATUS_TRANSITIONS.get(current_status, set()):
        raise InvalidTransitionError(current_status, next_status)
    task["status"] = next_status
    task["updated_at"] = now_iso()
    return task
