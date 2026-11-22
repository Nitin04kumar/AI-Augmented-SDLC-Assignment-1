import json
import os
import sys
from pathlib import Path

from .errors import TodoError, ValidationError
from .service import (
    add_task,
    change_status,
    delete_task,
    get_task,
    list_tasks,
    normalize_id,
    update_task,
)
from .store import read_store, write_store


def _emit_json(output, payload: object) -> None:
    output.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    output.write("\n")


def _parse_global_args(argv: list[str] | None) -> tuple[Path, list[str]]:  # pragma: no cover
    arguments = list(argv or [])
    data_path = Path(os.environ.get("TODO_DATA_FILE", "./tasks.json"))
    remaining: list[str] = []
    index = 0

    while index < len(arguments):
        token = arguments[index]
        if token == "--data":
            if index + 1 >= len(arguments):
                raise ValidationError("--data requires a path")
            data_path = Path(arguments[index + 1])
            index += 2
            continue
        if token.startswith("--data="):
            data_path = Path(token.split("=", 1)[1])
            index += 1
            continue
        remaining.append(token)
        index += 1

    return data_path, remaining


def _parse_add_arguments(
    arguments: list[str],
) -> tuple[str, str | None, str | None]:  # pragma: no cover
    title: str | None = None
    priority: str | None = None
    tags: str | None = None
    index = 0

    while index < len(arguments):
        token = arguments[index]
        if token in {"--priority", "--tags"}:
            if index + 1 >= len(arguments):
                raise ValidationError(f"{token} requires a value")
            value = arguments[index + 1]
            if token == "--priority":
                priority = value
            else:
                tags = value
            index += 2
            continue
        if token.startswith("--priority="):
            priority = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("--tags="):
            tags = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("--"):
            raise ValidationError(f"Unknown option: {token}")
        if title is not None:
            raise ValidationError("Task title may be supplied only once")
        title = token
        index += 1

    if title is None:
        raise ValidationError("Task title is required")
    return title, priority, tags


def _parse_update_arguments(
    arguments: list[str],
) -> tuple[str, dict[str, object]]:  # pragma: no cover
    if not arguments:
        raise ValidationError("update requires a task ID")
    task_id = arguments[0]
    updates: dict[str, object] = {}
    index = 1

    while index < len(arguments):
        token = arguments[index]
        if token in {"--title", "--priority", "--tags"}:
            if index + 1 >= len(arguments):
                raise ValidationError(f"{token} requires a value")
            value = arguments[index + 1]
            if token == "--title":
                updates["title"] = value
            elif token == "--priority":
                updates["priority"] = value
            elif token == "--tags":
                updates["tags"] = value
            index += 2
            continue
        if token.startswith("--title="):
            updates["title"] = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("--priority="):
            updates["priority"] = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("--tags="):
            updates["tags"] = token.split("=", 1)[1]
            index += 1
            continue
        raise ValidationError(f"Unknown option: {token}")

    if not updates:
        raise ValidationError("At least one field must be supplied for update")
    return task_id, updates


def _parse_list_arguments(
    arguments: list[str],
) -> tuple[str | None, str | None, str]:  # pragma: no cover
    tag: str | None = None
    status: str | None = None
    sort = "id"
    index = 0

    while index < len(arguments):
        token = arguments[index]
        if token in {"--tag", "--status", "--sort"}:
            if index + 1 >= len(arguments):
                raise ValidationError(f"{token} requires a value")
            value = arguments[index + 1]
            if token == "--tag":
                tag = value
            elif token == "--status":
                status = value
            else:
                sort = value
            index += 2
            continue
        if token.startswith("--tag="):
            tag = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("--status="):
            status = token.split("=", 1)[1]
            index += 1
            continue
        if token.startswith("--sort="):
            sort = token.split("=", 1)[1]
            index += 1
            continue
        raise ValidationError(f"Unknown option: {token}")

    return tag, status, sort


def _parse_status_arguments(arguments: list[str]) -> tuple[str, str]:  # pragma: no cover
    if len(arguments) != 2:
        raise ValidationError("status requires a task ID and a new status")
    return arguments[0], arguments[1]


def main(argv: list[str] | None = None) -> int:
    try:
        data_path, remaining = _parse_global_args(argv if argv is not None else sys.argv[1:])
        if not remaining:
            raise ValidationError("A command is required")

        command = remaining[0]
        rest = remaining[1:]
        store = read_store(data_path)

        if command == "add":
            title, priority, tags = _parse_add_arguments(rest)
            result = add_task(store, title, priority=priority, tags=tags)
            write_store(data_path, store)
            _emit_json(sys.stdout, result)
            return 0

        if command == "list":
            tag, status_value, sort = _parse_list_arguments(rest)
            result = list_tasks(store, tag=tag, status=status_value, sort=sort)
            _emit_json(sys.stdout, result)
            return 0

        if command == "get":
            if len(rest) != 1:
                raise ValidationError("get requires exactly one task ID")
            task_id = rest[0]
            normalize_id(task_id)
            result = get_task(store, task_id)
            _emit_json(sys.stdout, result)
            return 0

        if command == "update":
            task_id, updates = _parse_update_arguments(rest)
            result = update_task(store, task_id, **updates)
            write_store(data_path, store)
            _emit_json(sys.stdout, result)
            return 0

        if command == "delete":
            if len(rest) != 1:
                raise ValidationError("delete requires exactly one task ID")
            task_id = rest[0]
            normalize_id(task_id)
            result = delete_task(store, task_id)
            write_store(data_path, store)
            _emit_json(sys.stdout, result)
            return 0

        if command == "status":
            task_id, new_status = _parse_status_arguments(rest)
            result = change_status(store, task_id, new_status)
            write_store(data_path, store)
            _emit_json(sys.stdout, result)
            return 0

        raise ValidationError(f"Unknown command: {command}")
    except TodoError as exc:
        _emit_json(sys.stderr, exc.payload())
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive boundary
        _emit_json(sys.stderr, {"error": {"code": "VALIDATION_ERROR", "message": str(exc)}})
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
