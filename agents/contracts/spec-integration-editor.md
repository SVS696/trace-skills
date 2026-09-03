# Spec integration editor contract

## Assignment

Integrate all submitted artifacts for exactly one stage. The assignment must name
`case_root`, `stage`, `stage_reference`, `block_artifacts`, `previous_stitch`,
`report_output`, and `diff_output`.

## Rules

- Read only the named artifacts and this contract.
- Compare blocks; do not rewrite them during review.
- Produce one stitch report and one required-diff pool.
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
- Do not open side lists or make hidden corrections.
- An empty pool is valid only when the report states the checks performed and
  `deferred_inputs` is present, even when empty.

Return `ok`, `gap`, or `input-error` with both output paths, diff item ids and the exact
questions the parent must ask. `gap` always has at least one blocking diff item.
