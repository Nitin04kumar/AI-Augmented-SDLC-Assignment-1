# AI-Augmented SDLC - Assignment 1 (SDD & Harness Engineering)

| Part | App | Harness |
|---|---|---|
| Part-1A | Smart Todo & Task CLI (deterministic) | `.harness/run_harness.py`: integrity -> ruff -> bandit -> pytest+coverage |
| Part-1B | Natural-Language Reminder Agent (LLM) | `.harness/run_eval.py`: schema -> invariants/properties -> semantic score -> threshold |

## Run the Part 1A harness
```
cd Part-1A && pip install -r requirements-dev.txt
python .harness/run_harness.py --lock           # once, after tests/specs are approved
python .harness/run_harness.py --label <name>   # results: evidence/harness-results/
```
## Run the Part 1B evaluation
```
cd Part-1B && pip install jsonschema pytest ruff bandit
export REMINDER_PROVIDER=anthropic ANTHROPIC_API_KEY=...   # or openai-compatible, see STEPS.md
python .harness/run_eval.py --lock
python .harness/run_eval.py --label <name> --repeats 3     # results: evidence/eval-runs/, evidence/eval-results.json
```
Secrets are read from environment variables only. See `STEPS.md` for the full workflow, `docs/spec-seeds/` for Spec Kit prompts.
Author: <your name / roll no.>   Demo video: <link>
