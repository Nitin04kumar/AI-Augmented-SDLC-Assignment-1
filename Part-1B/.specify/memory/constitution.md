<!-- Sync Impact Report: Version change: initial -> 1.0.0; Modified principles: established the seven Natural-Language Reminder Agent principles from the Part 1B assignment seed; Added sections: Evaluation and Service Boundaries, Development Workflow and Quality Gates; Removed sections: none; Deferred items: none -->
# Natural-Language Reminder Agent Constitution

## Core Principles

### I. Contract-Bounded Behaviour
Behaviour is bounded by a machine-checkable Output Schema Contract and invariants, not by exact wording.

### II. Deterministic Guardrails
The model's text is untrusted data: every output passes deterministic guardrails before use.

### III. Prompt-Injection Resistance
User text is data, never instructions (prompt-injection resistance).

### IV. Secret Management
Secrets only via environment variables; never committed, never logged.

### V. Independent Evaluation
Evaluation is independent of the implementation: dataset, schema, thresholds and evaluators are read-only for the coding agent; the threshold is declared before evaluation and never lowered to obtain PASS.

### VI. Failure Classification
Model/service failures (HTTP/network/quota) are reported separately from application/eval failures.

### VII. Stack and Quality
Stack: Python >= 3.10, stdlib for the app, ruff + bandit clean, pytest for deterministic units.

## Evaluation and Service Boundaries

The Output Schema Contract and its invariants define acceptable outputs; exact wording is not an acceptance criterion. Model-produced content is never trusted until deterministic guardrails have validated it. User-provided text must not be interpreted as instructions to the agent.

Evaluation inputs and evaluators remain independent and read-only to the coding agent. Declare evaluation thresholds before running evaluation and do not lower them to obtain a passing result. Report failures caused by the model service separately from application and evaluation failures.

## Development Workflow and Quality Gates

The application targets Python 3.10 or newer and uses the Python standard library at runtime. Keep application code clean under ruff and bandit, and use pytest for deterministic unit tests.

Changes must preserve the Output Schema Contract, invariants, deterministic guardrails, and independent evaluation boundaries. Never commit or log secrets; obtain them only through environment variables.

## Governance

This constitution governs development of the Natural-Language Reminder Agent in Part 1B. Its seven core principles are authoritative. Amendments must preserve their meaning and record the rationale, version change, and impact on the project’s compliance expectations.

**Version**: 1.0.0 | **Ratified**: 2026-11-15 | **Last Amended**: 2026-11-15
