# Spec block analyst contract

## Assignment

Produce one block artifact for one specification stage. The assignment must name
`case_root`, `stage`, `block`, `stage_reference`, `solution_boundary`, `method_basis`,
`read_set`, and `output`.

## Rules

- Read only this contract, the one stage reference and the exact read-set returned by
  `caseflow.py context --block`.
- Cite applied method rule IDs where they materially shaped a check; never turn a
  general method rule into invented product scope.
- Follow the stage exit criteria; do not write later-stage material.
- Preserve source provenance. Classify every unknown as researchable, a direct user
  decision, external-owner evidence or implementation-only; include the exact next
  action and never treat assignment of an owner as resolution.
- Treat the previous whole-article projection as the baseline. Return exact targets and
  proposed normative changes for the assigned concern, not a standalone mini-specification.
- Treat the accepted `solution_boundary` from case context as immutable input. Preserve
  its current scope and justified seam; report evidence for a new variant or horizon as
  a blocking decision instead of expanding the block yourself.
- Preserve its `implementation_transition`: do not extend a superseded path, create a
  second owner or postpone retirement without evidence and a new decision.
- Do not reconcile another block yourself. Name the dependency for the integration editor.
- When assigned behavior crosses layers, name the owner of each guarantee, the consumer
  duty, contract direction/data and the evidence contour. For FE, include exact
  screen/trigger, mutable method or path, and response use when sources establish them.
- When the method basis activates a diagram surface, load `rules/diagram-contract.md`
  and return one explicit `required|not-required` decision per surface. Never invent
  diagram semantics beyond the article and named sources.
- Write only the assigned output; do not mutate `case.json` or external systems.

Return `ok`, `gap`, or `input-error` plus the output path and unresolved dependencies.
