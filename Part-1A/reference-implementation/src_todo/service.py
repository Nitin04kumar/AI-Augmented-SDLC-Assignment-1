"""Task business rules (spec FR-01 .. FR-07)."""

import re
from datetime import datetime, timezone

from todo import store
from todo.errors import NotFoundError, TransitionError, ValidationError

PRIORITIES = ("low", "medium", "high")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
STATUSES = ("todo", "in_progress", "done", "cancelled")
TRANSITIONS = {
    "todo": {"in_progress", "cancelled"},
    "in_progress": {"todo", "done", "cancelled"},
    "done": set(),
    "cancelled": set(),
}
MAX_TITLE = 100
MAX_TAGS = 10
TAG_RE = re.compile(r"^[a-z0-9_-]{1,20}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_title(title: str) -> str:
    cleaned = (title or "").strip()
    if not cleaned or len(cleaned) > MAX_TITLE:
        raise ValidationError(f"Title must be 1-{MAX_TITLE} characters after trimming")
    return cleaned


def normalize_tags(tags) -> list:
    result: list = []
    for raw in tags or []:
        tag = raw.strip().lower()
        if not TAG_RE.match(tag):
            raise ValidationError(f"Invalid tag: {raw!r}")
        if tag not in result:
            result.append(tag)
    if len(result) > MAX_TAGS:
        raise ValidationError(f"At most {MAX_TAGS} tags are allowed")
    return result


def normalize_priority(priority: str) -> str:
    if priority not in PRIORITIES:
        raise ValidationError(f"Priority must be one of {', '.join(PRIORITIES)}")
    return priority


def normalize_status(status: str) -> str:
    if status not in STATUSES:
        raise ValidationError(f"Status must be one of {', '.join(STATUSES)}")
    return status


def parse_id(raw) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Invalid task id: {raw!r}") from exc
    if value < 1:
        raise ValidationError(f"Invalid task id: {raw!r}")
    return value


class TaskService:
    def __init__(self, path: str):
        self.path = path
        self.data = store.load(path)

    def _find(self, task_id: int) -> dict:
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                return task
        raise NotFoundError(f"Task {task_id} not found")

    def _save(self) -> None:
        store.save(self.path, self.data)

    def add(self, title, priority="medium", tags=None) -> dict:
        task = {
            "id": self.data["next_id"],
            "title": normalize_title(title),
            "priority": normalize_priority(priority),
            "tags": normalize_tags(tags),
            "status": "todo",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.data["next_id"] += 1
        self.data["tasks"].append(task)
        self._save()
        return task

    def get(self, task_id) -> dict:
        return self._find(parse_id(task_id))

    def update(self, task_id, title=None, priority=None, tags=None) -> dict:
        task = self._find(parse_id(task_id))
        if title is None and priority is None and tags is None:
            raise ValidationError("Nothing to update")
        new_title = normalize_title(title) if title is not None else task["title"]
        new_priority = normalize_priority(priority) if priority is not None else task["priority"]
        new_tags = normalize_tags(tags) if tags is not None else task["tags"]
        task.update(
            title=new_title, priority=new_priority, tags=new_tags, updated_at=_now()
        )
        self._save()
        return task

    def delete(self, task_id) -> int:
        tid = parse_id(task_id)
        task = self._find(tid)
        self.data["tasks"].remove(task)
        self._save()
        return tid

    def set_status(self, task_id, status) -> dict:
        task = self._find(parse_id(task_id))
        new_status = normalize_status(status)
        if new_status not in TRANSITIONS[task["status"]]:
            raise TransitionError(f"Cannot move from {task['status']} to {new_status}")
        task["status"] = new_status
        task["updated_at"] = _now()
        self._save()
        return task

    def list_tasks(self, tag=None, status=None, sort="id") -> list:
        tasks = list(self.data["tasks"])
        if tag is not None:
            wanted = normalize_tags([tag])[0]
            tasks = [t for t in tasks if wanted in t["tags"]]
        if status is not None:
            wanted_status = normalize_status(status)
            tasks = [t for t in tasks if t["status"] == wanted_status]
        if sort == "priority":
            tasks.sort(key=lambda t: (PRIORITY_RANK[t["priority"]], t["id"]))
        elif sort == "id":
            tasks.sort(key=lambda t: t["id"])
        else:
            raise ValidationError("Sort must be 'id' or 'priority'")
        return tasks
