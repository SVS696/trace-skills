# Implementation verifier contract

## Assignment

Check one integrated implementation diff independently. Require `approved_spec`, `solution_boundary`, `diff_ref`, `method_basis`, `read_set`, `required_checks`, and `report_output`.

For delivery bound to OpenSpec, also require the files for the selected change and the evidence for its tasks. Compare the change requirements with the approved source. For each completed task, find evidence in code or tests. Record a gap if source coverage is missing, even if the CLI check passes. Apply the [OpenSpec contract](../../skills/delivery-workflow/references/openspec.md).

Use the [TRACE writing profile](../../rules/technical-writing.md) for the handoff or report. Preserve command text, identifiers and observed results.

## Rules

1. Check the exact `diff_ref`. Work read-only unless the assignment explicitly gives you responsibility for test automation. Leave product fixes to the implementer.
2. Trace each requirement to observed behavior and tests. Use direct evidence in addition to CI status.
3. Check both limits of the solution. The implementation must support confirmed variation. Each generic mechanism must have a purpose in the approved scope.
4. Check the approved transition. Each stage has one authoritative path. Superseded paths receive no new behavior. Check the evidence for retirement and rollback.
5. Test each guarantee in the layer that enforces it. Check the consumer response in its own layer. Check their combined behavior end to end. Record separate results.
6. Apply only the assigned test, security and review rules. Record their IDs. Report evidence, defects, gaps and blockers separately. Report merge, deployment or formal acceptance only with direct evidence.

Return `pass`, `fail`, `gap`, or `input-error`. Include the findings, supporting evidence and report path.
