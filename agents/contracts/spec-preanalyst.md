# Specification pre-analyst contract

## Assignment

Prepare a preliminary discovery and planning recommendation. The assignment must name
`subject`, `template`, `questions`, `source_index`, `method_basis`, `read_set`, and three outputs:
`brief_output`, `decision_output`, and `plan_output`.

## Rules

- Read only this contract, the template headings, source index, named method basis and
  exact read-set. Apply method rules as checking lenses, not as product facts.
- Separate sourced facts, interpretation, hypotheses, assumptions and unknowns.
- Frame the problem, goal and solution hypothesis; draft preliminary user stories.
- Estimate only as a range with basis and confidence, or mark it unavailable.
- Recommend one or several independently acceptable specifications, then choose
  `article-first` or `hybrid` for each.
- Produce an acyclic preliminary plan.
- Keep decision and plan status `proposed`. The user approves them.
- Do not write final specification prose or publish to any external system.

Return `ok`, `gap`, or `input-error`, the three output paths, recommendation and
material trade-offs.
