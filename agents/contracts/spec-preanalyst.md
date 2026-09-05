# Specification pre-analyst contract

## Assignment

Prepare a preliminary discovery and planning recommendation. The assignment must name
`subject`, `template`, `questions`, `source_index`, `method_basis`,
`solution_boundary_contract`, `read_set`, and three outputs: `brief_output`,
`decision_output`, and `plan_output`.

## Rules

- Read only this contract, the template headings, source index, named method basis and
  exact read-set. Apply method rules as checking lenses, not as product facts.
- Separate sourced facts, interpretation, hypotheses and assumptions. Classify every
  unknown as `researchable`, `user-decision`, `external-owner` or `implementation-only`.
- Investigate researchable inputs before returning. For a blocking user choice, return
  one direct question; for an external input, name its owner. Do not call a product or
  acceptance decision implementation-only.
- Frame the problem, goal and solution hypothesis; draft preliminary user stories.
- Apply `P04` through the assigned `rules/solution-boundary.md`. Choose
  `tactical|bounded-systemic|generalized-capability`, distinguish confirmed variants
  from hypotheses, and check both `particular-case` and `speculative-generalization`.
  Preserve an evidence-backed localized extension seam, or explain why none is useful.
  Do not promote deferred variants into current scope.
- Estimate only as a range with basis and confidence, or mark it unavailable.
- Recommend one or several independently acceptable specifications. Every article uses
  `article-led` composition: define semantic blocks only for focused passes after the
  first whole-template draft.
- Produce an acyclic preliminary plan.
- Keep decision and plan status `proposed`. The user approves them.
- Do not write final specification prose or publish to any external system.

Return `ok`, `gap`, or `input-error`, the three output paths, recommendation, material
trade-offs and the batched direct questions the parent must ask. `ok` is forbidden while
a researchable input has not been investigated.
