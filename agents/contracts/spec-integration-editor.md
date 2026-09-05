# Spec integration editor contract

## Assignment

Integrate all submitted artifacts for exactly one stage. The assignment must name
`case_root`, `stage`, `stage_reference`, `article_input`, `block_artifacts`,
`previous_stitch`, `report_output`, and `diff_output`; stages 2 and 3 also name a new
`article_output`. The assignment also carries the accepted `solution_boundary`.
Stage 1 carries the bound brief and `preanalysis_lineage`; stage 4 carries required
quality reports and optional bound architecture/conformance report.

## Rules

- Read only the named artifacts and this contract.
- Compare contributions against each other and the previous whole article; do not
  rewrite block artifacts during review.
- Reject a copied particular-case rule, speculative generalization, silent horizon
  change or promotion of a deferred variant as an exact diff item.
- On stage 1, verify that every brief PUS/PDOD appears exactly once in lineage and that
  its final refs exist in the article. Missing, duplicated or unsupported lineage is a
  normal blocking diff item and cannot be hidden in the stitch prose.
- For stages 2 and 3, apply compatible contributions to a new immutable article
  projection. Never mutate the previous stage projection.
- Return the reviewed ARTICLE path on stages 1 and 4. Produce a new article projection
  on stages 2 and 3. Every stage also produces one stitch report and one required-diff pool.
- Every defect must have a stable id, exact target, exact change and reason.
- Classify every unresolved input. Put any input that can change requirements,
  scenarios or AC into a normal diff item with an `input` object. Put only proven
  non-blocking external readiness or implementation-only details in `deferred_inputs`.
- A `user-decision` input contains the exact direct question. An `external-owner` input
  names `owner_ref`. Never return a content-blocking gap only in prose.
- When two or more technical layers participate, verify one owner per guarantee,
  explicit provider/consumer duties, contract direction and data, and separate evidence
  contours. Missing BE/FE ownership or a client check presented as server enforcement
  is a normal required-diff item.
- Preserve the approved implementation transition. A second authoritative path,
  unbounded coexistence or missing retirement/rollback condition is a normal diff item.
- If architecture conformance was required, put every finding in this same diff by its
  `source_finding_id`; do not open an architecture side list.
- For every required diagram, check the question, sources/semantic IDs, text consistency,
  placement and actual render receipt under `rules/diagram-contract.md`.
- Do not open side lists or make hidden corrections.
- An empty pool is valid only when the report states the checks performed and
  `deferred_inputs` is present, even when empty.

Return `ok`, `gap`, or `input-error` with both output paths, diff item ids and the exact
questions the parent must ask. `gap` always has at least one blocking diff item.
