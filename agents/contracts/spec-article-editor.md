# Spec article editor contract

## Assignment

Create or consolidate one complete reader-facing article. The assignment must name
`stage`, `template`, `previous_article` when stage 4, `read_set`, `method_basis`, and
`solution_boundary`, and `article_output`.

## Rules

- Keep the template headings and their order unchanged.
- On stage 1, walk the whole template and make the end-to-end model visible before any
  semantic block pass. Do not produce disconnected placeholders for later assembly.
- On stage 4, consolidate the integrated stage 3 article; do not reconstruct it from
  independent block artifacts.
- Resolve no unlisted gap by invention; surface every content gap as a blocking current-stage
  diff item with its evidence need or direct user question. Do not turn it into polished
  reader prose or a non-blocking backlog.
- Remove block ids, process findings and internal state from reader-facing prose.
- Preserve provenance and traceability required by the project.
- Preserve the accepted root capability, current scope, invariants and evidence-backed
  extension seam. Do not promote deferred or hypothesized variants, change the horizon,
  or publish the internal horizon id in reader-facing prose.
- Preserve established layer scopes, responsibility matrices, interface handoffs,
  requirement owners and separate BE/FE/E2E acceptance evidence. Map them into the
  unchanged template instead of flattening them into a generic implementation list.
- Use only the named requirements-writing/review method basis; do not open the full
  Vigers library.
- Write only the article output. Review and process-state changes belong to the parent.

Return `ok`, `gap`, or `input-error` with the output path and surfaced gaps.
