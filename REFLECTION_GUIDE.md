# Part 2 reflection - what to write (you must write the answers yourself)

The AI policy lists "auto-generating your reflection or log entries" as unacceptable, so this file only tells you
which of YOUR OWN evidence to cite. Fill the attached Word template (Assignment_Submission-Template) by hand, and
add the GitHub repo link and demo video link in it.

1. Specification influence - pick one decision in your code and walk: artifact section -> task id -> file/function.
   (e.g. a constitution rule, a clarify answer such as "done is terminal", or a plan decision.) Cite file paths.
2. Harness value (1A) - pick one issue that a harness gate caught (name the gate, rule/test id, run file). Say why a
   self-review by the agent could miss it (e.g. coverage threshold, a modified-test integrity hit, a bandit rule, a
   boundary like exactly 100 characters). If your run had no failure, use a gate that would have caught a planned
   regression you actually tried in a scratch copy and say that honestly.
3. Non-determinism (1B) - choose one case (e.g. TC-01, TC-18). Name the schema constraint (OSC-1 field/enum), the
   invariant/property (INV-02 / PROP-forbidden ...), and the semantic criterion (time fidelity, title recall) and why
   exact string matching would fail (many valid titles/wordings).
4. Feedback and self-healing - one real repair cycle: the feedback file you gave the agent, what changed in the diff, and
   whether integrity gate/threshold stayed untouched.
5. Human accountability - one residual risk after PASS (small dataset, model drift, timezone/locale, no auth, prompt
   injection variants not covered), your ACCEPT/REJECT call, and one extra control (more eval cases, canary monitoring,
   human confirmation before scheduling, rate limiting, red-team set, etc.).
