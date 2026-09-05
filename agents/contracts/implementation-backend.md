# Implementation backend contract

## Assignment

Implement one approved backend lane. The assignment must name `requirements`,
`solution_boundary`, `owned_paths`, `shared_contracts`, `method_basis`, `required_checks`,
and `handoff_output`.

## Rules

- Work only inside `owned_paths`; coordinate before touching shared files.
- Trace every change to an assigned requirement.
- Implement only `current_scope`, preserve the accepted localized extension seam, and
  do not build deferred variants or change the solution horizon inside the lane.
- Follow the approved `implementation_transition`: keep its authoritative owner, do not
  add behavior to superseded paths, and satisfy named retirement/rollback conditions.
- Own only guarantees assigned to Backend and expose the approved shared contract.
  Never rely on Frontend filtering, hidden controls or client validation as enforcement.
- Apply only the named delivery rule basis; project canon outranks general literature.
- Add or update developer tests proportional to the change.
- Preserve unrelated and concurrent edits; never reset another worker's changes.
- Do not claim independent verification, merge, deploy or acceptance.

Return changed paths, commands and results, unresolved gaps, and the handoff path.
