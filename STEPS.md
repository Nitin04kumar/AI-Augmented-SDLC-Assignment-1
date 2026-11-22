# Step-by-step: finish Assignment 1 (about 2-3 hours)

What is already built for you: tests, harness runners, eval dataset (20 cases), schema, thresholds, evaluators,
Spec Kit prompt packs, log templates, traceability tables, and a working reference implementation (to prove the
tooling works - NOT your evidence). What only YOU can produce: Spec Kit artifacts, the agent's first implementation,
real model evaluation runs, harness-log entries, reflection answers, demo video, GitHub repo.

## 0. Setup (10 min)
1. Python 3.10+, git, `pip install -r requirements-dev.txt` (Part-1A) and `pip install jsonschema pytest ruff bandit` (Part-1B).
2. Install Spec Kit as in Lab Sheet 1 (`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`) and have your coding agent ready.
3. Create a model key for Part 1B (see step 4) - keep it in an environment variable ONLY.
4. `git init` inside Assignment-1/ and create a PUBLIC GitHub repo (empty for now).

## 1. Part 1A (60-75 min)
1. `cd Part-1A && specify init . --ai <your-agent>` (answer "merge/continue" if it asks about existing files; keep tests/, .harness/, evidence/).
2. Run /speckit.constitution -> specify -> clarify -> plan -> tasks -> analyze using `docs/spec-seeds/part1a.md`.
   Read and edit each output; commit after each command (commit history = change history).
3. If your specify output changed any ID/behaviour, update the spec through Spec Kit; only if truly required change tests, then re-lock and note it.
4. `python .harness/run_harness.py --lock`  (freezes tests, harness config, specs).
5. Run /speckit.implement with the restrictions in the seed file. Then immediately:
   `python .harness/run_harness.py --snapshot initial`
   `python .harness/run_harness.py --label initial`
6. If any gate FAILS: open `evidence/harness-results/run-001-initial-feedback.md`, give that file to the agent ("fix src only"),
   then `python .harness/run_harness.py --label repair-1` (repeat as needed). Never edit tests/harness/results to get a PASS.
   If it passes first time, don't fake a failure - just document that.
7. When all gates PASS: `python .harness/run_harness.py --snapshot final` and `--label final`.
8. Fill `evidence/harness-log.md` by hand; extend `evidence/traceability.md` with spec/task/src columns; record your ACCEPT/REJECT.

## 2. Part 1B (60-75 min)
1. Pick a model: easiest free options - Gemini via OpenAI-compatible URL, Groq, or local Ollama; or Anthropic key.
   Examples (bash):
   - Anthropic:  `export REMINDER_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-...  REMINDER_MODEL=claude-haiku-4-5`
   - Gemini:     `export REMINDER_PROVIDER=openai OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai OPENAI_API_KEY=... REMINDER_MODEL=gemini-2.0-flash`
   - Ollama:     `export REMINDER_PROVIDER=openai OPENAI_BASE_URL=http://localhost:11434/v1 REMINDER_MODEL=llama3.1`
   (Check current model names in the provider's docs.) Never put the key in a file.
2. `cd Part-1B && specify init . --ai <your-agent>`; run the Spec Kit flow with `docs/spec-seeds/part1b.md`.
3. `python .harness/run_eval.py --lock` then /speckit.implement (restricted), then
   `python .harness/run_eval.py --snapshot initial` and `python .harness/run_eval.py --label initial --repeats 3`.
4. Read `evidence/eval-runs/run-001-initial.json`. If FAIL: give `...-feedback.md` to the agent, let it repair src/prompts only, run
   `--label repair-1`. If INCONCLUSIVE it was API trouble (quota/auth) - fix the service issue and re-run; do not touch the app.
5. When PASS: `--snapshot final`, `--label final --repeats 3`. `evidence/eval-results.json` always holds the latest run.
6. `pytest tests` for deterministic unit tests, and `ruff`/`bandit` as in Part 1A (optional but good).
7. Fill `evidence/harness-log.md` by hand. Do not weaken thresholds or dataset. You may ADD cases only via a documented spec change before the final run.
   Note: `--lock` covers the dataset, so adding cases means re-lock + a note in the log.

## 3. Repo, video, report (30 min)
1. Check no secrets: `grep -rEi "api[_-]?key|sk-" . --include="*" -l` (should list only docs mentioning env var names), no `.env` files.
2. Update README.md run commands if your layout differs; `git add -A && git commit && git push` to the PUBLIC repo.
3. Demo video (2-4 min, screen recording): show the spec artifacts, run Part 1A harness, show a failure->repair if you had one, run Part 1B eval, show result + your decision. Upload to Drive/OneDrive, share with BITS emails.
4. Complete the Word reflection template by hand (see REFLECTION_GUIDE.md), include GitHub link + video link, upload ONLY that file to LMS before 15 Nov 2026 deadline.

## Checklist from the assignment
Both parts present | Spec Kit artifacts | working gates + spec-derived tests | >=15 eval cases + one pipeline | results & failure/repair evidence | harness-log.md both | ACCEPT/REJECT + limitations | no secrets | run instructions.
