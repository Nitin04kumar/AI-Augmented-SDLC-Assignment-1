"""Spec-derived contract tests. Each test cites the acceptance criterion (AC) it verifies.

AC IDs come from the feature specification (see docs/spec-seeds/part1a-specify.md).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ---------- FR-01 add ----------


def test_ac01_add_defaults(cli):
    """AC-01: add sets id=1, priority=medium, status=todo, empty tags."""
    code, out, _ = cli("add", "Buy milk")
    assert code == 0
    assert out["id"] == 1
    assert out["title"] == "Buy milk"
    assert out["priority"] == "medium"
    assert out["status"] == "todo"
    assert out["tags"] == []


def test_ac02_title_is_trimmed(cli):
    """AC-02: surrounding whitespace in title is trimmed."""
    _, out, _ = cli("add", "   padded   ")
    assert out["title"] == "padded"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 101])
def test_ac03_invalid_title_rejected(cli, bad):
    """AC-03: empty/blank/over-100-char title -> exit 1, VALIDATION_ERROR."""
    code, out, err = cli("add", bad)
    assert code == 1
    assert out is None
    assert err["error"]["code"] == "VALIDATION_ERROR"


def test_ac03_title_boundary_100_ok(cli):
    """AC-03: exactly 100 characters is accepted."""
    code, out, _ = cli("add", "x" * 100)
    assert code == 0
    assert len(out["title"]) == 100


def test_ac04_ids_sequential_and_never_reused(cli):
    """AC-04: ids increase; a deleted id is never reassigned."""
    cli("add", "a")
    cli("add", "b")
    cli("delete", "2")
    _, out, _ = cli("add", "c")
    assert out["id"] == 3


def test_ac05_invalid_priority_rejected(cli):
    """AC-05: priority must be low|medium|high."""
    code, _, err = cli("add", "t", "--priority", "urgent")
    assert code == 1
    assert err["error"]["code"] == "VALIDATION_ERROR"


# ---------- FR-02 tags ----------


def test_ac06_tags_normalised_and_deduplicated(cli):
    """AC-06: tags are lower-cased, trimmed, de-duplicated, order preserved."""
    _, out, _ = cli("add", "t", "--tags", "Work, home ,WORK,urgent")
    assert out["tags"] == ["work", "home", "urgent"]


@pytest.mark.parametrize("bad", ["bad tag", "a" * 21, "semi;colon", "ünï"])
def test_ac07_invalid_tag_rejected(cli, bad):
    """AC-07: tag must match [a-z0-9_-]{1,20}."""
    code, _, err = cli("add", "t", "--tags", bad)
    assert code == 1
    assert err["error"]["code"] == "VALIDATION_ERROR"


def test_ac08_max_ten_tags(cli):
    """AC-08: 10 tags accepted, 11 rejected."""
    ten = ",".join(f"t{i}" for i in range(10))
    eleven = ten + ",t10"
    assert cli("add", "ok", "--tags", ten)[0] == 0
    assert cli("add", "no", "--tags", eleven)[0] == 1


# ---------- FR-03 / FR-04 list, filter, sort ----------


def _seed(cli):
    cli("add", "low-1", "--priority", "low", "--tags", "home")
    cli("add", "high-1", "--priority", "high", "--tags", "work")
    cli("add", "med-1", "--priority", "medium", "--tags", "work,home")
    cli("add", "high-2", "--priority", "high")


def test_ac09_list_default_order_by_id(cli):
    """AC-09: list without options is ordered by id ascending."""
    _seed(cli)
    _, out, _ = cli("list")
    assert out["count"] == 4
    assert [t["id"] for t in out["tasks"]] == [1, 2, 3, 4]


def test_ac10_filter_by_tag(cli):
    """AC-10: --tag returns only tasks carrying that tag (case-insensitive)."""
    _seed(cli)
    _, out, _ = cli("list", "--tag", "WORK")
    assert [t["id"] for t in out["tasks"]] == [2, 3]


def test_ac11_filter_by_status(cli):
    """AC-11: --status filters on status."""
    _seed(cli)
    cli("status", "1", "in_progress")
    _, out, _ = cli("list", "--status", "in_progress")
    assert [t["id"] for t in out["tasks"]] == [1]


def test_ac12_sort_by_priority_high_first_ties_by_id(cli):
    """AC-12: --sort priority orders high>medium>low, ties by ascending id."""
    _seed(cli)
    _, out, _ = cli("list", "--sort", "priority")
    assert [t["id"] for t in out["tasks"]] == [2, 4, 3, 1]


def test_ac13_filter_and_sort_combine(cli):
    """AC-13: tag filter and priority sort can be combined."""
    _seed(cli)
    _, out, _ = cli("list", "--tag", "home", "--sort", "priority")
    assert [t["id"] for t in out["tasks"]] == [3, 1]


def test_ac14_invalid_sort_or_status_filter_rejected(cli):
    """AC-14: unknown sort key or status filter -> exit 1."""
    assert cli("list", "--sort", "bogus")[0] == 1
    assert cli("list", "--status", "bogus")[0] == 1


# ---------- FR-05 get / update ----------


def test_ac15_get_existing_and_missing(cli):
    """AC-15: get returns the task; unknown id -> exit 2 NOT_FOUND."""
    cli("add", "a")
    code, out, _ = cli("get", "1")
    assert code == 0 and out["title"] == "a"
    code, _, err = cli("get", "99")
    assert code == 2
    assert err["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("bad_id", ["abc", "0", "-3", "1.5"])
def test_ac16_malformed_id_is_validation_error(cli, bad_id):
    """AC-16: non-positive / non-integer id -> exit 1."""
    code, _, err = cli("get", bad_id)
    assert code == 1
    assert err["error"]["code"] == "VALIDATION_ERROR"


def test_ac17_update_changes_only_given_fields(cli):
    """AC-17: update modifies only supplied fields; tags are replaced, not merged."""
    cli("add", "old", "--priority", "low", "--tags", "a,b")
    _, out, _ = cli("update", "1", "--title", "new")
    assert (out["title"], out["priority"], out["tags"]) == ("new", "low", ["a", "b"])
    _, out, _ = cli("update", "1", "--tags", "c")
    assert out["tags"] == ["c"]
    _, out, _ = cli("update", "1", "--tags", "")
    assert out["tags"] == []


def test_ac18_update_requires_a_field_and_validates(cli):
    """AC-18: update with no fields or invalid values -> exit 1 and task unchanged."""
    cli("add", "keep")
    assert cli("update", "1")[0] == 1
    assert cli("update", "1", "--title", " ")[0] == 1
    assert cli("update", "1", "--priority", "nope")[0] == 1
    _, out, _ = cli("get", "1")
    assert out["title"] == "keep"
    assert cli("update", "42", "--title", "x")[0] == 2


# ---------- FR-06 delete ----------


def test_ac19_delete(cli):
    """AC-19: delete removes the task; second delete -> exit 2."""
    cli("add", "a")
    code, out, _ = cli("delete", "1")
    assert code == 0 and out == {"deleted": 1}
    assert cli("get", "1")[0] == 2
    assert cli("delete", "1")[0] == 2


# ---------- FR-07 status transitions ----------

ALLOWED = [
    ("todo", "in_progress"),
    ("todo", "cancelled"),
    ("in_progress", "todo"),
    ("in_progress", "done"),
    ("in_progress", "cancelled"),
]
FORBIDDEN = [
    ("todo", "done"),
    ("todo", "todo"),
    ("in_progress", "in_progress"),
    ("done", "todo"),
    ("done", "in_progress"),
    ("done", "cancelled"),
    ("cancelled", "todo"),
    ("cancelled", "done"),
]
PATH = {
    "todo": [],
    "in_progress": ["in_progress"],
    "done": ["in_progress", "done"],
    "cancelled": ["cancelled"],
}


def _reach(cli, state):
    cli("add", "t")
    for step in PATH[state]:
        assert cli("status", "1", step)[0] == 0


@pytest.mark.parametrize(("src", "dst"), ALLOWED)
def test_ac20_allowed_transitions(cli, src, dst):
    """AC-20: every allowed transition succeeds and updates status."""
    _reach(cli, src)
    code, out, _ = cli("status", "1", dst)
    assert code == 0 and out["status"] == dst


@pytest.mark.parametrize(("src", "dst"), FORBIDDEN)
def test_ac21_forbidden_transitions(cli, src, dst):
    """AC-21: every other transition -> exit 3 INVALID_TRANSITION, status unchanged."""
    _reach(cli, src)
    code, _, err = cli("status", "1", dst)
    assert code == 3
    assert err["error"]["code"] == "INVALID_TRANSITION"
    assert cli("get", "1")[1]["status"] == src


def test_ac22_unknown_status_value(cli):
    """AC-22: unknown status name -> exit 1; unknown task -> exit 2."""
    cli("add", "t")
    assert cli("status", "1", "finished")[0] == 1
    assert cli("status", "9", "done")[0] == 2


# ---------- FR-08 persistence ----------


def test_ac23_persists_between_invocations(cli, data_file):
    """AC-23: state is stored as JSON and survives across invocations."""
    cli("add", "persist", "--tags", "x")
    stored = json.loads(data_file.read_text(encoding="utf-8"))
    assert stored["next_id"] == 2
    assert stored["tasks"][0]["title"] == "persist"
    assert cli("get", "1")[1]["tags"] == ["x"]


def test_ac24_corrupt_file_exit_4_and_untouched(cli, data_file):
    """AC-24: corrupt JSON -> exit 4 STORAGE_ERROR and the file is not modified."""
    data_file.write_text("{not json", encoding="utf-8")
    code, _, err = cli("add", "x")
    assert code == 4
    assert err["error"]["code"] == "STORAGE_ERROR"
    assert data_file.read_text(encoding="utf-8") == "{not json"


def test_ac24_wrong_structure_exit_4(cli, data_file):
    """AC-24: valid JSON with wrong structure is treated as storage error."""
    data_file.write_text('{"tasks": "oops"}', encoding="utf-8")
    assert cli("list")[0] == 4


def test_ac25_failed_command_does_not_modify_file(cli, data_file):
    """AC-25: a rejected command leaves the data file byte-identical."""
    cli("add", "a")
    before = data_file.read_bytes()
    cli("add", "")
    cli("status", "1", "done")
    cli("delete", "77")
    assert data_file.read_bytes() == before


def test_ac26_no_temp_files_left_behind(cli, data_file):
    """AC-26: atomic write leaves no *.tmp files in the data directory."""
    cli("add", "a")
    cli("update", "1", "--title", "b")
    assert list(data_file.parent.glob("*.tmp")) == []


# ---------- FR-09 output contract ----------


def test_ac27_task_object_shape(cli):
    """AC-27: task JSON exposes exactly the documented fields."""
    _, out, _ = cli("add", "shape")
    assert set(out) == {"id", "title", "priority", "tags", "status", "created_at", "updated_at"}


def test_ac28_unknown_command_is_validation_error(cli):
    """AC-28: argument errors are reported as JSON on stderr with exit 1."""
    code, out, err = cli("explode")
    assert code == 1 and out is None
    assert err["error"]["code"] == "VALIDATION_ERROR"


def test_ac29_module_entrypoint(tmp_path):
    """AC-29: `python -m todo` works as a process and honours exit codes."""
    data = tmp_path / "t.json"
    src_dir = Path(__file__).resolve().parents[1] / "src"
    env = {**os.environ, "PYTHONPATH": str(src_dir)}
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "todo", "--data", str(data), "add", "proc"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["title"] == "proc"
    bad = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "todo", "--data", str(data), "get", "99"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env=env,
    )
    assert bad.returncode == 2
