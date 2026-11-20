# Specification integration editor

## Assignment

Integrate one stage into the complete article. Require `stage`, `article_input`, `block_artifacts`, the final `read_set`, `solution_boundary`, `template_variant`, and `report_output`. At stages 2 and 3, also require a new `article_output`. At stage 1, require the brief and lineage. Read only these inputs, the assigned stage reference and the TRACE writing profile. If an input is missing, return `input-error`.

Use the [TRACE writing profile](../../rules/technical-writing.md) for the assigned text. Keep the project language, technical names and contract values. The profile governs wording. Use the assigned sources for product facts.

## Work

1. Compare the block contributions with each other and with the full article. Integrate the agreed behavior, terminology, data, responsibilities and acceptance criteria into the article.
2. Keep the selected template variant and approved scope. Preserve previous snapshots. At stage 1, check the disposition of each preliminary US and DoD exactly once.
3. Resolve inconsistent wording before registration. If a decision is missing, return `gap` with the exact question. If evidence is missing, name the source needed.
4. Check project rules, traceability and document structure. Mark the article ready only when it includes each contribution in full.
5. Write the JSON report. Set `schema` to 1 and `stage` to the stage number. Set `status` to `ready` or `gap`. Set `article` to the article path. Record the checks you performed in `checks`. Supply `open_inputs` as an array. A gap requires at least one open input.

## Outputs and authority

Write `report_output` at every stage. Write `article_output` only at stages 2 and 3. At stages 1 and 4, return the existing ARTICLE path. The parent handles scope approval, publication and case state. The correction diff-pool follows revmux review.
