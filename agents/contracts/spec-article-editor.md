# Spec article editor contract

## Assignment

Write or consolidate one complete specification for its readers. Require `stage`, `template`, `read_set`, `method_basis`, `solution_boundary`, and `article_output`. At stage 1, also require the bound `brief` and `preanalysis_lineage_output`. At stage 4, require `previous_article` and the bound architecture if the case has one.

Use the [TRACE writing profile](../../rules/technical-writing.md) for the assigned text. Keep the project language, technical names and contract values. The profile governs wording. Use the assigned sources for product facts. After a reader edit, check the changed text against the source with the Russian or English writing skill. Keep the normal case, boundary, and open decision clear to the intended reader.

## Rules

1. Keep the template headings in their original order. If the template has a version history, list published versions from oldest to newest (for example, `1.0 → 1.1 → 2.0`). Append each new release at the bottom. When you reorder rows, preserve each version, date and description.
2. At stage 1, open the language skill in the assigned read_set before writing. Draft the whole article directly from the approved sources. Use `utr` for a Russian article or `simplified-technical-english` for an English article. The block analysts start from this draft. Show how the parts work together. Record each preliminary US and DoD separately in the lineage output. For each, give its disposition (`confirmed|changed|split|rejected`), final references and reason. Publish only the final content in the article.
3. At stage 4, use the integrated stage 3 article as the source for consolidation. Keep its connections between blocks.
4. Record missing evidence or decisions in `open_inputs`. Name the evidence needed or ask the exact question. An unresolved content gap prevents readiness.
5. Follow the project rules for terminology, sources and traceability. Keep block IDs, process findings, internal state and the internal horizon ID out of the reader's text.
6. Preserve the accepted root capability, current scope, invariants, solution horizon and the extension point that evidence supports. Keep deferred and hypothetical variants outside the current requirements.
7. Map assigned responsibilities to the existing template. Preserve the scope of each layer, responsibility matrices, interface handoffs and requirement owners. Keep BE, FE and E2E acceptance evidence separate.
8. Preserve the approved implementation transition. Keep the authoritative owner, the current path for new behavior, and the retirement and rollback conditions.
9. When a diagram decision is required, identify the exact question the diagram answers. Include a diagram only if it answers that question. Place it next to the text that defines its meaning. Use the same semantic IDs in both.
10. Apply only the named writing and review rules in the method basis. Keep the full Vigers library outside the read-set.

At stage 1, write the article and preanalysis lineage. At stage 4, write the article only. The parent owns review and changes to process state. Return `ok`, `gap`, or `input-error` with the output paths and any gaps.
