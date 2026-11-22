#!/usr/bin/env python3
"""Part 1B single evaluation harness.

dataset -> app/model call -> schema validation -> invariants/properties -> semantic scoring
        -> aggregate vs declared thresholds -> PASS/FAIL (+ structured failure evidence)

Usage:
  python .harness/run_eval.py --lock                      # freeze dataset/thresholds/evaluators/specs
  python .harness/run_eval.py --label initial [--repeats 3]
  python .harness/run_eval.py --snapshot initial          # copy src/ + prompts/ into evidence/
Env: REMINDER_PROVIDER=anthropic|openai|mock, REMINDER_MODEL, REMINDER_TEMPERATURE, API keys.
Exit codes: 0 PASS, 1 FAIL, 2 INCONCLUSIVE (model-service failures), 3 integrity violation.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / ".harness"
sys.path[:0] = [str(HARNESS), str(ROOT / "src")]

from evaluators import properties, semantic, structural  # noqa: E402

from reminder_agent.agent import parse_request  # noqa: E402
from reminder_agent.llm import ModelServiceError, get_client  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
THRESHOLDS = HARNESS / "thresholds.json"
RUNS = ROOT / "evidence" / "eval-runs"
LOCK = HARNESS / "protected.lock.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected() -> dict:
    files = [DATASET, THRESHOLDS, HARNESS / "run_eval.py", HARNESS / "schema" / "output.schema.json"]
    files += sorted((HARNESS / "evaluators").glob("*.py"))
    for extra in ("specs", ".specify/memory"):
        files += sorted(p for p in (ROOT / extra).rglob("*.md")) if (ROOT / extra).exists() else []
    return {str(p.relative_to(ROOT)): sha(p) for p in files if p.exists()}


def integrity_issues() -> list:
    if not LOCK.exists():
        return [{"rule": "missing-lock", "message": "run --lock first"}]
    locked = json.loads(LOCK.read_text())["files"]
    now = protected()
    issues = []
    for name in sorted(set(locked) | set(now)):
        if locked.get(name) != now.get(name):
            kind = "removed" if name not in now else "added" if name not in locked else "modified"
            issues.append({"rule": f"protected-file-{kind}", "file": name})
    return issues


def evaluate_case(case: dict, client, repeats: int, th: dict) -> dict:
    attempts, service_errors = [], 0
    for _ in range(repeats):
        ctx = case["input"]
        try:
            res = parse_request(ctx["text"], ctx["now"], ctx["timezone"], ctx.get("existing_reminder"), client)
        except ModelServiceError as exc:
            service_errors += 1
            attempts.append({"service_error": str(exc)})
            continue
        out = res["output"]
        l1 = structural.check(out)
        l2 = [] if l1 else properties.invariants(out, ctx) + properties.case_properties(out, case["expected"])
        sem = semantic.score(out, case["expected"]) if not l1 else {"components": {}, "score": 0.0}
        gates_ok = not l1 and not l2
        attempts.append({
            "output": out, "raw_model_output": res["raw"][:1500], "guardrail_actions": res["actions"],
            "structural_violations": l1, "property_violations": l2, "semantic": sem,
            "case_score": sem["score"] if gates_ok else 0.0,
            "passed": gates_ok and sem["score"] >= th["case_semantic_pass_min"],
        })
    scored = [a for a in attempts if "service_error" not in a]
    if not scored:
        return {"id": case["id"], "category": case["category"], "status": "SERVICE_ERROR",
                "requirements": case["requirements"], "attempts": attempts}
    return {
        "id": case["id"], "category": case["category"], "requirements": case["requirements"],
        "status": "PASS" if all(a["passed"] for a in scored) else "FAIL",
        "structural_ok": all(not a["structural_violations"] for a in scored),
        "properties_ok": all(not a["property_violations"] for a in scored),
        "case_score": sum(a["case_score"] for a in scored) / len(scored),
        "attempts": attempts,
    }


def aggregate(results: list, th: dict) -> dict:
    scored = [r for r in results if r["status"] != "SERVICE_ERROR"]
    n = len(scored) or 1
    safety = [r for r in scored if r["category"] in th["safety_categories"]]
    metrics = {
        "cases_total": len(results), "cases_scored": len(scored),
        "service_errors": len(results) - len(scored),
        "service_error_ratio": (len(results) - len(scored)) / (len(results) or 1),
        "structural_pass_rate": sum(r["structural_ok"] for r in scored) / n,
        "property_pass_rate": sum(r["properties_ok"] for r in scored) / n,
        "safety_property_pass_rate": (sum(r["properties_ok"] for r in safety) / len(safety)) if safety else 1.0,
        "quality_score": sum(r["case_score"] for r in scored) / n,
        "cases_passed": sum(r["status"] == "PASS" for r in scored),
    }
    checks = {
        "structural": metrics["structural_pass_rate"] >= th["structural_pass_rate_min"],
        "safety": metrics["safety_property_pass_rate"] >= th["safety_property_pass_rate_min"],
        "quality": metrics["quality_score"] >= th["aggregate_quality_score_min"],
    }
    if metrics["service_error_ratio"] > th["max_service_error_ratio"]:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS" if all(checks.values()) else "FAIL"
    return {"metrics": metrics, "threshold_checks": checks, "decision": decision}


def write_feedback(path: Path, run: dict) -> None:
    lines = [f"# Eval feedback - run {run['run']} ({run['label']}) - {run['aggregate']['decision']}", "",
             "Repair src/ and/or prompts/ ONLY. Do not edit evals/, .harness/, thresholds or specs.",
             f"Aggregate: `{json.dumps(run['aggregate']['metrics'])}`",
             f"Threshold checks: `{json.dumps(run['aggregate']['threshold_checks'])}`", ""]
    for r in run["cases"]:
        if r["status"] != "FAIL":
            continue
        case = next(c for c in run["_dataset"] if c["id"] == r["id"])
        att = next(a for a in r["attempts"] if "service_error" not in a and not a["passed"])
        lines += [f"## {r['id']} [{r['category']}] requirements={r['requirements']}",
                  f"Input: {json.dumps(case['input'])}", f"Expected: {json.dumps(case['expected'])}",
                  f"Rubric: {case['rubric']}", f"Generated output: {json.dumps(att['output'])}",
                  f"Structural violations: {json.dumps(att['structural_violations'])}",
                  f"Property violations: {json.dumps(att['property_violations'])}",
                  f"Semantic: {json.dumps(att['semantic'])}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def snapshot(label: str) -> None:
    dest = ROOT / "evidence" / f"{label}-generation"
    if dest.exists():
        shutil.rmtree(dest)
    for part in ("src", "prompts"):
        shutil.copytree(ROOT / part, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    files = {str(p.relative_to(dest)): sha(p) for p in sorted(dest.rglob("*")) if p.is_file()}
    (dest / "MANIFEST.json").write_text(json.dumps(
        {"label": label, "created": datetime.now(timezone.utc).isoformat(), "files": files}, indent=2))
    print(f"Snapshot saved to {dest}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--snapshot", metavar="LABEL")
    args = ap.parse_args()
    if args.lock:
        LOCK.write_text(json.dumps({"created": datetime.now(timezone.utc).isoformat(), "files": protected()}, indent=2))
        print(f"Locked {len(protected())} files")
        return 0
    if args.snapshot:
        snapshot(args.snapshot)
        return 0
    if not args.label:
        ap.error("--label is required")

    issues = integrity_issues()
    if issues:
        print("INTEGRITY VIOLATION:", json.dumps(issues, indent=2))
        return 3
    th = json.loads(THRESHOLDS.read_text())
    dataset = json.loads(DATASET.read_text())["cases"]
    client = get_client()
    results = [evaluate_case(c, client, args.repeats, th) for c in dataset]
    agg = aggregate(results, th)
    RUNS.mkdir(parents=True, exist_ok=True)
    run_no = len(list(RUNS.glob("run-*[0-9]-*.json"))) + 1
    run = {
        "run": run_no, "label": args.label, "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {**client.describe(), "repeats": args.repeats, "dataset_sha256": sha(DATASET)},
        "thresholds": th, "aggregate": agg, "cases": results,
    }
    stem = f"run-{run_no:03d}-{args.label}"
    (RUNS / f"{stem}.json").write_text(json.dumps(run, indent=2))
    (ROOT / "evidence" / "eval-results.json").write_text(json.dumps(run, indent=2))
    if agg["decision"] in ("FAIL", "INCONCLUSIVE"):
        write_feedback(RUNS / f"{stem}-feedback.md", {**run, "_dataset": dataset})
    m = agg["metrics"]
    for r in results:
        print(f"{r['status']:<13} {r['id']} [{r['category']}] score={r.get('case_score', 0):.2f}")
    print(f"quality={m['quality_score']:.3f} structural={m['structural_pass_rate']:.2f} "
          f"safety={m['safety_property_pass_rate']:.2f} service_errors={m['service_errors']}")
    print(f"DECISION: {agg['decision']}  (provider={run['config']['provider']})  -> evidence/eval-runs/{stem}.json")
    return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}[agg["decision"]]


if __name__ == "__main__":
    sys.exit(main())
