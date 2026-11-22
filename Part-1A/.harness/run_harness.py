#!/usr/bin/env python3
"""Part 1A deterministic harness runner.

Gates (all mandatory):
  1. integrity  - tests/, harness config and specs match the recorded lock (anti-weakening)
  2. lint       - ruff
  3. security   - bandit (medium+ severity)
  4. tests      - pytest + coverage threshold

Usage:
  python .harness/run_harness.py --lock                 # record protected-file hashes
  python .harness/run_harness.py --label initial        # run all gates, save evidence
  python .harness/run_harness.py --snapshot initial     # copy src/ to evidence/initial-generation/
Exit code 0 = all gates PASS, 1 = at least one gate FAILED.
Results are written by this script only; never edit them by hand.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / ".harness"
RESULTS = ROOT / "evidence" / "harness-results"
LOCK = HARNESS / "protected.lock.json"
COVERAGE_MIN = 85
TAIL = 4000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_files() -> list:
    files = [p for p in (ROOT / "tests").rglob("*.py")]
    files += [HARNESS / "run_harness.py", HARNESS / "ruff.toml"]
    for extra in ("specs", ".specify/memory"):
        base = ROOT / extra
        if base.exists():
            files += [p for p in base.rglob("*.md") if p.is_file()]
    return sorted({p for p in files if p.exists()})


def current_hashes() -> dict:
    return {str(p.relative_to(ROOT)): sha256(p) for p in protected_files()}


def run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        cmd, cwd=ROOT, capture_output=True, text=True, check=False, timeout=600
    )


def gate_result(name, cmd, proc, issues, started) -> dict:
    failed = bool(issues) or bool(proc and proc.returncode != 0)
    if failed and not issues and proc:
        issues = [
            {
                "rule": "gate-failed-without-parsed-issue",
                "message": ((proc.stdout or "") + (proc.stderr or ""))[-1500:],
            }
        ]
    return {
        "gate": name,
        "command": " ".join(cmd) if cmd else "(internal)",
        "exit_code": proc.returncode if proc else 0,
        "status": "FAIL" if failed else "PASS",
        "duration_s": round(time.time() - started, 2),
        "issues": issues,
        "stdout_tail": (proc.stdout or "")[-TAIL:] if proc else "",
        "stderr_tail": (proc.stderr or "")[-TAIL:] if proc else "",
    }


def gate_integrity() -> dict:
    started = time.time()
    issues = []
    if not LOCK.exists():
        issues.append({"rule": "missing-lock", "message": "Run with --lock first"})
    else:
        locked = json.loads(LOCK.read_text(encoding="utf-8"))["files"]
        now = current_hashes()
        for name in sorted(set(locked) | set(now)):
            if name not in now:
                issues.append({"rule": "protected-file-removed", "file": name})
            elif name not in locked:
                issues.append({"rule": "protected-file-added", "file": name})
            elif locked[name] != now[name]:
                issues.append({"rule": "protected-file-modified", "file": name})
    res = gate_result("integrity", None, None, issues, started)
    res["status"] = "FAIL" if issues else "PASS"
    return res


def gate_lint() -> dict:
    started = time.time()
    cmd = [
        sys.executable,
        "-m",
        "ruff",
        "check",
        "src",
        "tests",
        ".harness",
        "--config",
        ".harness/ruff.toml",
        "--output-format",
        "json",
    ]
    proc = run(cmd)
    issues = []
    try:
        for item in json.loads(proc.stdout or "[]"):
            issues.append(
                {
                    "rule": item.get("code"),
                    "message": item.get("message"),
                    "file": str(Path(item["filename"]).relative_to(ROOT)),
                    "line": item["location"]["row"],
                }
            )
    except (ValueError, KeyError):
        pass
    return gate_result("lint", cmd, proc, issues, started)


def gate_security() -> dict:
    started = time.time()
    cmd = [sys.executable, "-m", "bandit", "-r", "src", "-ll", "-f", "json", "-q"]
    proc = run(cmd)
    issues = []
    try:
        for item in json.loads(proc.stdout or "{}").get("results", []):
            issues.append(
                {
                    "rule": item["test_id"],
                    "severity": item["issue_severity"],
                    "message": item["issue_text"],
                    "file": item["filename"],
                    "line": item["line_number"],
                }
            )
    except ValueError:
        pass
    return gate_result("security", cmd, proc, issues, started)


def gate_tests(out_dir: Path, label: str) -> dict:
    started = time.time()
    junit = out_dir / f"{label}-junit.xml"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-q",
        f"--junitxml={junit}",
        "--cov=todo",
        "--cov-report=term-missing",
        f"--cov-fail-under={COVERAGE_MIN}",
    ]
    proc = run(cmd)
    issues = []
    if junit.exists():
        for case in ET.parse(junit).getroot().iter("testcase"):  # noqa: S314
            for kind in ("failure", "error"):
                node = case.find(kind)
                if node is not None:
                    issues.append(
                        {
                            "rule": "test-failed",
                            "test": f"{case.get('classname')}::{case.get('name')}",
                            "message": (node.get("message") or "")[:500],
                            "detail": (node.text or "")[:1500],
                        }
                    )
    if "FAIL Required test coverage" in (proc.stdout or ""):
        issues.append(
            {"rule": "coverage-below-threshold", "message": f"coverage below {COVERAGE_MIN}%"}
        )
    return gate_result("tests", cmd, proc, issues, started)


def write_feedback(path: Path, result: dict) -> None:
    lines = [
        f"# Harness feedback - run {result['run']} ({result['label']})",
        "",
        "Fix src/ only. Do NOT edit tests/, specs/, .harness/ or lint/security config.",
        "",
    ]
    for gate in result["gates"]:
        if gate["status"] == "PASS":
            continue
        lines += [f"## Gate: {gate['gate']} - FAIL", f"Command: `{gate['command']}`", ""]
        for issue in gate["issues"]:
            lines.append("- " + json.dumps(issue))
        if gate["gate"] == "tests":
            lines += ["", "Output tail:", "```", gate["stdout_tail"][-2500:], "```"]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def snapshot(label: str) -> None:
    dest = ROOT / "evidence" / f"{label}-generation"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(ROOT / "src", dest / "src", ignore=shutil.ignore_patterns("__pycache__"))
    manifest = {str(p.relative_to(dest)): sha256(p) for p in sorted(dest.rglob("*")) if p.is_file()}
    manifest_doc = {
        "label": label,
        "created": datetime.now(timezone.utc).isoformat(),
        "files": manifest,
    }
    (dest / "MANIFEST.json").write_text(json.dumps(manifest_doc, indent=2), encoding="utf-8")
    print(f"Snapshot saved to {dest}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", help="e.g. initial, repair-1, final")
    ap.add_argument("--lock", action="store_true")
    ap.add_argument("--snapshot", metavar="LABEL")
    args = ap.parse_args()

    if args.lock:
        LOCK.write_text(
            json.dumps(
                {"created": datetime.now(timezone.utc).isoformat(), "files": current_hashes()},
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Locked {len(current_hashes())} protected files -> {LOCK}")
        return 0
    if args.snapshot:
        snapshot(args.snapshot)
        return 0
    if not args.label:
        ap.error("--label is required")

    RESULTS.mkdir(parents=True, exist_ok=True)
    run_no = len(list(RESULTS.glob("run-*.json"))) + 1
    gates = [
        gate_integrity(),
        gate_lint(),
        gate_security(),
        gate_tests(RESULTS, f"run-{run_no:03d}-{args.label}"),
    ]
    overall = "PASS" if all(g["status"] == "PASS" for g in gates) else "FAIL"
    result = {
        "run": run_no,
        "label": args.label,
        "overall": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "protected_hashes": current_hashes(),
        "gates": gates,
    }
    stem = f"run-{run_no:03d}-{args.label}"
    (RESULTS / f"{stem}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if overall == "FAIL":
        write_feedback(RESULTS / f"{stem}-feedback.md", result)
    for g in gates:
        print(f"[{g['status']}] {g['gate']:<10} issues={len(g['issues'])}  ({g['duration_s']}s)")
    print(f"OVERALL: {overall}  -> evidence/harness-results/{stem}.json")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
