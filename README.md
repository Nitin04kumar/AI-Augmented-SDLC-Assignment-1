# AI-Augmented SDLC – Assignment 1

## Spec-Driven Development (SDD) & Harness Engineering

This repository contains the implementation of Assignment 1, demonstrating **Spec-Driven Development (SDD)** and **Harness Engineering** through two Python applications.

## Project Overview

| Part    | Application                     | Development Approach                                      | Harness                   |
| ------- | ------------------------------- | --------------------------------------------------------- | ------------------------- |
| Part 1A | Smart Todo & Task CLI           | Deterministic, specification-driven development           | `.harness/run_harness.py` |
| Part 1B | Natural-Language Reminder Agent | AI/LLM-assisted development with deterministic guardrails | `.harness/run_eval.py`    |

### Part 1A – Smart Todo & Task CLI

A command-line task management application developed using Python.

**Key components:**

- Project constitution and specification.
- Implementation plan and task breakdown.
- CLI contract and data model.
- Task creation and management functionality.
- Deterministic validation and error handling.
- Automated testing and code quality checks.

**Harness workflow:**

`Integrity → Ruff → Bandit → Pytest + Coverage`

**Final reported validation:**

- 50 tests passed.
- Code coverage: 95.34%.
- Integrity, lint, security and test gates passed.

### Part 1B – Natural-Language Reminder Agent

An AI-powered reminder application that interprets natural-language instructions and produces structured reminder actions.

**Key components:**

- Natural-language request processing.
- LLM integration through a configurable provider.
- Deterministic guardrails and validation.
- Reminder creation, rescheduling and snoozing.
- Ambiguity and missing-information handling.
- Prompt engineering and structured JSON output.
- Adversarial input and boundary-case evaluation.

**Harness workflow:**

`Schema → Invariants / Properties → Semantic Evaluation → Threshold Decision`

**Final Groq evaluation results:**

| Metric                  | Result |
| ----------------------- | -----: |
| Evaluation cases passed |  20/20 |
| Quality score           |  1.000 |
| Structural score        |   1.00 |
| Safety score            |   1.00 |
| Service errors          |      0 |
| Final decision          |   PASS |

Unit tests: 16 passed.

Mock evaluation: 20/20 passed.

## Repository Structure

```text
Assignment-1/
│
├── Part-1A/
│   ├── .harness/
│   ├── .specify/
│   ├── specs/
│   ├── src/todo/
│   ├── tests/
│   ├── evidence/
│   └── requirements-dev.txt
│
├── Part-1B/
│   ├── .harness/
│   ├── .specify/
│   ├── specs/
│   ├── prompts/
│   ├── src/reminder_agent/
│   ├── tests/
│   ├── evals/
│   ├── evidence/
│   └── requirements-dev.txt
│
├── docs/
│   └── spec-seeds/
│
├── README.md
├── REFLECTION_GUIDE.md
└── STEPS.md
```

## Technologies Used

- Python
- Spec Kit
- Git and GitHub
- Pytest
- Ruff
- Bandit
- JSON Schema
- Large Language Models (LLMs)
- Groq API through an OpenAI-compatible interface

## Setup and Execution

### Prerequisites

- Python 3.10 or later
- pip
- Git
- API key for a supported LLM provider when running real-provider evaluations

### Part 1A – Install and Run

```bash
cd Part-1A

pip install -r requirements-dev.txt
```

Create the protected-file integrity lock once, after approving the tests and specifications:

```bash
python .harness/run_harness.py --lock
```

Run the harness:

```bash
python .harness/run_harness.py --label final-run
```

Harness results are stored in:

```text
Part-1A/evidence/harness-results/
```

### Part 1B – Install and Run

```bash
cd Part-1B

pip install -r requirements-dev.txt
```

Create the protected-file integrity lock once, after approving the evaluation setup:

```bash
python .harness/run_eval.py --lock
```

#### Run with Mock Provider

```bash
REMINDER_PROVIDER=mock PYTHONPATH=src \
python .harness/run_eval.py --label mock-evaluation
```

#### Run with Groq API

The application uses an OpenAI-compatible provider configuration for Groq.

```bash
export REMINDER_PROVIDER=openai
export OPENAI_BASE_URL=https://api.groq.com/openai/v1
export REMINDER_MODEL=openai/gpt-oss-120b
export REMINDER_TEMPERATURE=0.3
```

Enter the API key securely:

```bash
read -rsp "Enter Groq API Key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY
```

Run the evaluation:

```bash
PYTHONPATH=src python .harness/run_eval.py --label groq-evaluation
```

For repeated evaluation:

```bash
PYTHONPATH=src python .harness/run_eval.py \
  --label repeated-evaluation --repeats 3
```

Evaluation artifacts are stored in:

```text
Part-1B/evidence/eval-runs/
Part-1B/evidence/eval-results.json
```

### Run Unit Tests

```bash
cd Part-1B
python -m pytest tests/test_agent_units.py -q
```

### Run Code Quality Checks

```bash
ruff check --config .harness/ruff.toml src
```

## Evidence and Documentation

The repository preserves development and evaluation evidence, including:

- Initial and final generation snapshots.
- Specification, plan and task artifacts.
- Harness execution logs.
- Evaluation run JSON files.
- Feedback from earlier evaluation runs.
- Requirement-to-test traceability.
- Protected-file integrity lock files.

Important Part 1B evaluation records:

```text
Part-1B/evidence/eval-runs/
├── run-011-tc13-weekday-mock.json
└── run-012-groq-reschedule-fix.json
```

## Security

- API credentials are supplied through environment variables.
- Secret files such as `.env` are excluded using `.gitignore`.
- API keys should never be committed to GitHub.
- Deterministic guardrails validate LLM-generated outputs.
- Protected harness and evaluation files are integrity-checked.

## Demo Video

**Demonstration Video:** https://drive.google.com/file/d/1VXO8_JgcXpFdWZfrIpnsjUebblkML0aP/view?usp=sharing

The demonstration covers:

1. Project overview and repository structure.
2. Part 1A specifications and implementation.
3. Part 1A harness execution and results.
4. Part 1B specifications and implementation.
5. Part 1B mock and real-provider evaluations.
6. Harness evidence and GitHub repository walkthrough.

## Author

**Name:** Nitin Kumar  
**BITS ID:** 2026NS93097  
**Assignment:** AI-Augmented SDLC – Assignment 1

## References

- [GitHub Repository](https://github.com/Nitin04kumar/AI-Augmented-SDLC-Assignment-1)
- [Spec Kit](https://github.com/github/spec-kit)
- [Python Documentation](https://docs.python.org/3/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Groq Documentation](https://console.groq.com/docs)
