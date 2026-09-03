# Quality pass reviewer contract

## Assignment

Run exactly one assigned gate: `simplicity-spec`, `humanizer`, or
`simplicity-code`. The assignment names the subject and its SHA-256, the exact
peer-skill entrypoint, bounded project rules, the required checks from
`rules/quality-pass.md`, and `report_output`. A `humanizer` assignment also names
the applicable style profile; a `simplicity-code` assignment also names required
runnable checks.

## Rules

- Read and execute only the assigned peer skill; reading or naming it is not a pass.
- Do not edit the subject. Return exact proposed changes for the current diff-pool.
- Inspect the real artifact and preserve safety, evidence, public contracts,
  traceability, and tested edge cases.
- Run every check required for the selected gate, including the full style cycle for
  `humanizer` and the real-flow check for `simplicity-code`.
- Findings name an exact target, required change, reason, and stable id.

Return `clean`, `changes-required`, or `input-error` with one schema-1 observable
quality report.
