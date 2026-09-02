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
- Do not open side lists or make hidden corrections.
- An empty pool is valid only when the report states the checks performed.

Return `ok`, `gap`, or `input-error` with both output paths and the diff item ids.
