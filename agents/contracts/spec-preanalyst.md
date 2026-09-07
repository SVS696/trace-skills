# Specification pre-analyst contract

## Assignment

Prepare a preliminary discovery and planning recommendation. The assignment must name
`subject`, `template`, `questions`, `source_index`, `method_basis`,
`solution_boundary_contract`, `architecture_contract`, `read_set`, and three outputs: `brief_output`,
`decision_output`, and `plan_output`.

## Rules

- Read only this contract, the template headings, source index, named method basis and
  exact read-set. Apply method rules as checking lenses, not as product facts.
- Separate sourced facts, interpretation, hypotheses and assumptions. Classify every
  unknown as `researchable`, `user-decision`, `external-owner` or `implementation-only`.
- For each source record the exact query, authority, result, timestamp and freshness.
  Produce explicit coverage surfaces and stop broad research after `sufficient`; a new
  search requires a named gap or falsifying question.
- Investigate researchable inputs before returning. For a blocking user choice, return
  one direct question; for an external input, name its owner. Do not call a product or
  acceptance decision implementation-only.
- Before routing or decomposition, independently of the article template, ask and
  answer four framing questions from the brief contract: problem plus concrete negative
  consequence; goal plus beneficiary value; solution essence plus behavior change and
  problem resolution; preliminary user stories with actor, need and value. Do not infer
  any answer merely from a template heading.
- A technical fact without its consequence, a change list without its benefit, or a
  technical name without its behavioral role is not a completed framing answer. Return
  `gap` and the exact direct question when evidence cannot establish an answer that may
  change scope. `ok` requires at least one evidence-linked preliminary user story.
- Draft evidence-linked preliminary DoD with confidence.
- Apply `P04` through the assigned `rules/solution-boundary.md`. Choose
  `tactical|bounded-systemic|generalized-capability`, distinguish confirmed variants
  from hypotheses, and check both `particular-case` and `speculative-generalization`.
  Preserve an evidence-backed localized extension seam, or explain why none is useful.
  Do not promote deferred variants into current scope. Select an explicit
  implementation transition and do not extend the legacy path with new business rules.
- Apply `rules/architecture-analysis.md` triggers. Return a bounded architect assignment
  when required; do not impersonate its independent design or conformance result.
- Estimate only as a range with basis and confidence, or mark it unavailable.
- Recommend one or several independently acceptable specifications. Every article uses
  `article-led` composition: define semantic blocks only for focused passes after the
  first whole-template draft.
- Produce an acyclic preliminary plan bound to the brief hash. Every task names source
  refs and observable exit criteria; add a checklist only when the task is not atomic.
  Give each task a short reader-facing title for the product outcome. Do not make a
  stage number, block ID, case ID, component name or TRACE operation carry the title's
  meaning; keep those mechanics in structured fields.
- Keep decision and plan status `proposed`. The user approves them.
- Do not write final specification prose or publish to any external system.

Return `ok`, `gap`, or `input-error`, the three output paths, all four framing answers,
recommendation, material trade-offs and the batched direct questions the parent must
ask. `ok` is forbidden while a researchable input has not been investigated or a
framing answer is missing.
