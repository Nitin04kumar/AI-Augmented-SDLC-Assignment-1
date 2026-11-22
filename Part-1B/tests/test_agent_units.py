"""Deterministic unit tests for the non-AI parts: guardrails, JSON extraction, harness evaluators."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / ".harness")]

from evaluators import properties, semantic, structural  # noqa: E402

from reminder_agent.agent import parse_request  # noqa: E402
from reminder_agent.llm import extract_json  # noqa: E402

NOW = "2026-11-16T09:00:00+05:30"


class FakeClient:
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def complete(self, system, user):
        self.calls += 1
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def valid_create(**over):
    base = {
        "intent": "create", "title": "Call mom", "remind_at": "2026-11-17T18:00:00+05:30",
        "recurrence": None, "needs_clarification": False, "missing_fields": [],
        "clarification_question": None, "refusal_reason": None, "confidence": 0.9,
    }
    base.update(over)
    return base


def test_g01_blank_input_never_calls_model():
    client = FakeClient(valid_create())
    res = parse_request("   ", NOW, "Asia/Kolkata", None, client)
    assert client.calls == 0
    assert res["output"]["intent"] == "clarify"


def test_g01_oversize_input_refused_without_model_call():
    client = FakeClient(valid_create())
    res = parse_request("x" * 501, NOW, "Asia/Kolkata", None, client)
    assert client.calls == 0 and res["output"]["intent"] == "refuse"


def test_g02_sentinel_leak_blocked():
    leak = valid_create(title="RA-SYS-7731 secret")
    out = parse_request("remind me", NOW, "Asia/Kolkata", None, FakeClient(leak))["output"]
    assert out["intent"] == "refuse"


def test_g03_snooze_without_existing_becomes_clarify():
    reply = valid_create(intent="snooze")
    out = parse_request("snooze", NOW, "Asia/Kolkata", None, FakeClient(reply))["output"]
    assert out["intent"] == "clarify" and out["missing_fields"] == ["target_reminder"]


@pytest.mark.parametrize("when", ["2026-11-16T09:00:00+05:30", "2020-01-01T10:00:00+05:30",
                                  "2026-11-17T18:00:00", "garbage", "2040-01-01T10:00:00+05:30"])
def test_g04_g05_bad_times_become_clarify(when):
    out = parse_request("x", NOW, "Asia/Kolkata", None, FakeClient(valid_create(remind_at=when)))["output"]
    assert out["intent"] == "clarify" and out["remind_at"] is None


def test_valid_output_passes_through_unchanged():
    reply = valid_create()
    res = parse_request("remind me", NOW, "Asia/Kolkata", None, FakeClient(reply))
    assert res["output"] == reply and res["actions"] == []


def test_unparseable_model_output_is_safe_clarify():
    res = parse_request("remind me", NOW, "Asia/Kolkata", None, FakeClient("I cannot do JSON"))
    assert res["output"]["intent"] == "clarify"


def test_extract_json_handles_fences_and_prose():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} done') == {"a": 2}
    assert extract_json("no json") is None


# ---- the harness evaluators must themselves detect bad outputs ----

def test_structural_layer_detects_violations():
    bad = valid_create(intent="delete_all", extra="x")
    assert structural.check(bad)
    assert structural.check(valid_create()) == []


def test_property_layer_detects_past_time_and_missing_offset():
    ctx = {"now": NOW, "existing_reminder": None}
    assert properties.invariants(valid_create(remind_at="2020-01-01T10:00:00+05:30"), ctx)
    assert properties.invariants(valid_create(remind_at="2026-11-17T18:00:00"), ctx)
    assert properties.invariants(valid_create(), ctx) == []


def test_property_layer_detects_leakage_and_bad_clarify():
    ctx = {"now": NOW, "existing_reminder": None}
    leaked = valid_create(intent="refuse", title=None, remind_at=None, refusal_reason="RA-SYS-7731")
    assert any(v["rule"] == "INV-07" for v in properties.invariants(leaked, ctx))
    bad_clarify = valid_create(intent="clarify", remind_at=None)
    assert any(v["rule"] == "INV-03" for v in properties.invariants(bad_clarify, ctx))


def test_semantic_layer_scores_time_and_title():
    exp = {"remind_at": "2026-11-17T18:00:00+05:30", "tolerance_minutes": 0,
           "title_keywords": ["call", "mom"]}
    assert semantic.score(valid_create(), exp)["score"] == 1.0
    off = semantic.score(valid_create(remind_at="2026-11-17T09:00:00+05:30", title="Call"), exp)
    assert 0 < off["score"] < 1
