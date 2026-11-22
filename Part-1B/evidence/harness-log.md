# Part 1B harness log  (WRITE THIS YOURSELF from your real runs - do not paste AI-written text)

## 1. Model / configuration (no secrets!)
- Provider: ______  Model: ______  Temperature: ______  Repeats: ______  (copy from evidence/eval-runs/run-*.json -> config)
- Dataset sha256 (from config): ______   Number of cases: ______

## 2. Threshold and scoring (declared BEFORE final evaluation - quote from spec.md / .harness/thresholds.json)
- Structural pass rate >= ____ | Safety property pass rate >= ____ | Aggregate quality >= ____
- Case score: ______

## 3. Runs
| Run | Label | Structural | Property/invariant | Semantic/quality | Quality score | Service errors | Decision | File |
|---|---|---|---|---|---|---|---|---|
| 1 | initial | | | | | | | |

## 4. Failures and repair (only real ones)
- Failing case ids and categories: ______
- Evidence given to the coding agent (path to run-NNN-*-feedback.md + prompt used): ______
- What changed (prompt / parser / guardrail / code): ______
- Re-evaluation outcome vs previous run: ______
- Was a service/model failure ever mixed up with an app failure? How were they separated? ______

## 5. Final human review
- Decision: ACCEPT / REJECT      Justification: ______
- Known limitations and residual risks (e.g. dataset size, model drift, single timezone): ______
