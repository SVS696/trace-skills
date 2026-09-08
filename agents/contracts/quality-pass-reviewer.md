# Quality pass reviewer contract

## Assignment

Run exactly one assigned gate: `simplicity-spec`, `humanizer`, or
`simplicity-code`. The assignment names the subject and its SHA-256, the exact
peer-skill entrypoint, bounded project rules, the required checks from
`rules/quality-pass.md`, and `report_output`. A `humanizer` assignment also names
the applicable style profile; a `simplicity-code` assignment also names required
runnable checks.

For `purpose: revmux-finding-adjudication`, the subject is the exact `revmux` receipt.
The assignment also provides only the evidence needed to inspect each finding against
the current requirement or real execution flow. Apply `simplicity-spec` to article
findings and `simplicity-code` to implementation findings.

## Rules

- Read and execute only the assigned peer skill; reading or naming it is not a pass.
- Do not edit the subject. Return exact proposed changes for the current diff-pool.
- Inspect the real artifact and preserve safety, evidence, public contracts,
  traceability, and tested edge cases.
- Run every check required for the selected gate, including the full style cycle for
  `humanizer` and the real-flow check for `simplicity-code`.
- For `simplicity-spec`, include the change-boundary check within
  `element-classification` as defined in `rules/quality-pass.md` and the assigned
  skill. Preserving a public contract means preserving compatibility, not retaining
  its unchanged description as work scope. Bound the verdict to the actual read-set.
- Findings name an exact target, required change, reason, and stable id.
- In finding adjudication, account for every receipt finding exactly once. Keep a
  confirmed finding in `findings` with the smallest sufficient correction; put a
  speculative, unreachable or disproportionate finding in `dismissed_finding_ids`
  with its evidence in the report. Do not re-review the whole subject.

Return `clean`, `changes-required`, or `input-error` with one schema-1 observable
quality report.
