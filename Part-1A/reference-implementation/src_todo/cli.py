"""Command line interface. Success -> JSON on stdout; errors -> JSON on stderr."""

import argparse
import json
import os
import sys

from todo.errors import TodoError, ValidationError
from todo.service import TaskService


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValidationError(message)


def _split_tags(raw):
    if raw is None:
        return None
    return [part for part in raw.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="todo")
    parser.add_argument("--data", default=os.environ.get("TODO_DATA_FILE", "tasks.json"))
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    add = sub.add_parser("add")
    add.add_argument("title")
    add.add_argument("--priority", default="medium")
    add.add_argument("--tags", default=None)

    lst = sub.add_parser("list")
    lst.add_argument("--tag", default=None)
    lst.add_argument("--status", default=None)
    lst.add_argument("--sort", default="id")

    get = sub.add_parser("get")
    get.add_argument("id")

    upd = sub.add_parser("update")
    upd.add_argument("id")
    upd.add_argument("--title", default=None)
    upd.add_argument("--priority", default=None)
    upd.add_argument("--tags", default=None)

    dele = sub.add_parser("delete")
    dele.add_argument("id")

    stat = sub.add_parser("status")
    stat.add_argument("id")
    stat.add_argument("new_status")
    return parser


def _dispatch(args) -> dict:
    svc = TaskService(args.data)
    if args.command == "add":
        return svc.add(args.title, args.priority, _split_tags(args.tags))
    if args.command == "list":
        tasks = svc.list_tasks(args.tag, args.status, args.sort)
        return {"count": len(tasks), "tasks": tasks}
    if args.command == "get":
        return svc.get(args.id)
    if args.command == "update":
        return svc.update(args.id, args.title, args.priority, _split_tags(args.tags))
    if args.command == "delete":
        return {"deleted": svc.delete(args.id)}
    return svc.set_status(args.id, args.new_status)


def main(argv=None) -> int:
    try:
        args = build_parser().parse_args(argv)
        result = _dispatch(args)
    except TodoError as exc:
        err = {"error": {"code": exc.code, "message": str(exc)}}
        print(json.dumps(err), file=sys.stderr)
        return exc.exit_code
    print(json.dumps(result))
    return 0
