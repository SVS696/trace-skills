# Implementation frontend contract

## Assignment

Implement one approved frontend lane. The assignment must name `requirements`,
`solution_boundary`, `owned_paths`, `shared_contracts`, `method_basis`, `required_checks`,
and `handoff_output`.

For OpenSpec-bound delivery or new direct implementation, also require `openspec_root`,
`openspec_change`, assigned `openspec_tasks` and their package read-set. Read the shared
[OpenSpec contract](../../skills/delivery-workflow/references/openspec.md). Missing
inputs return `input-error` before coding; legacy unbound delivery remains unchanged.

## Rules

- Work only inside `owned_paths`; coordinate before touching shared files.
- Implement only `current_scope`, preserve the accepted localized extension seam, and
  do not build deferred variants or change the solution horizon inside the lane.
- Follow the approved `implementation_transition`: keep its authoritative owner, do not
  add behavior to superseded paths, and satisfy named retirement/rollback conditions.
- Bind behavior to the exact screen, trigger, mutable method/path and response use.
- Implement only the assigned consumer duties. Do not reconstruct authoritative server
  state, add local fallback data or treat hidden controls as Backend enforcement unless
  the approved specification explicitly requires it.
- Reuse the project design system and established patterns.
- Apply only the named delivery rule basis; project canon outranks general literature.
- Add or update developer tests proportional to the change.
- Preserve unrelated and concurrent edits; never reset another worker's changes.
- Do not claim independent verification, merge, deploy or acceptance.

Return task-number → changed paths → commands/results, unresolved gaps, and the handoff
path. The parent owns shared OpenSpec checkbox updates and archive; do not edit them
concurrently from a lane.
