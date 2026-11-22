# Reference implementation (NOT your evidence)

Used by the assignment author to verify that `tests/` and `.harness/` are correct and runnable.
Your submission's `src/` must come from YOUR `/speckit.implement` run, and `evidence/initial-generation/`
must hold that first output. Do not present this folder as agent output or as your own work.

Sanity check of the tooling only:
    mkdir -p /tmp/ref && cp -r ../* /tmp/ref/ && cd /tmp/ref && mkdir -p src && cp -r reference-implementation/src_todo src/todo
    python .harness/run_harness.py --lock && python .harness/run_harness.py --label ref-check
