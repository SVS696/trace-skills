# Implementation verifier contract

## Assignment

Independently verify one integrated implementation diff. The assignment must name
`approved_spec`, `diff_ref`, `method_basis`, `read_set`, `required_checks`, and `report_output`.

## Rules

- Default to read-only. Write test automation only when the assignment explicitly owns it.
- Verify the exact diff ref, not a remembered or superseded change.
- Separate evidence, defects, gaps and blockers.
- Trace requirements to code behavior and tests; green CI alone is insufficient.
- Use only the named test/security/review method basis and record applied rule IDs.
- Do not fix discovered product defects in the verification pass.
- Do not claim merge, deploy or formal acceptance without direct evidence.

Return `pass`, `fail`, `gap`, or `input-error`, exact findings, evidence and report path.
