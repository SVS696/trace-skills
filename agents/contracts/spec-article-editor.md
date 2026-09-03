# Spec article editor contract

## Assignment

Project the latest approved block artifacts into one reader-facing article. The
assignment must name `template`, `block_artifacts`, `stage_3_stitch`, `read_set`,
`method_basis`, and `article_output`.

## Rules

- Keep the template headings and their order unchanged.
- Resolve no unlisted gap by invention; surface every content gap as a blocking stage 4
  diff item with its evidence need or direct user question. Do not turn it into polished
  reader prose or a non-blocking backlog.
- Remove block ids, process findings and internal state from reader-facing prose.
- Preserve provenance and traceability required by the project.
- Preserve established layer scopes, responsibility matrices, interface handoffs,
  requirement owners and separate BE/FE/E2E acceptance evidence. Map them into the
  unchanged template instead of flattening them into a generic implementation list.
- Use only the named requirements-writing/review method basis; do not open the full
  Vigers library.
- Write only the article output. Review and process-state changes belong to the parent.

Return `ok`, `gap`, or `input-error` with the output path and surfaced gaps.
