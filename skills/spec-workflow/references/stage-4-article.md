# Stage 4: Article and review

**Entry:** Stage 3 diff-pool is closed and case stage is `4`.

1. The article editor projects the latest block artifacts into the unchanged template.
   The public article contains no block-process ids, findings or internal state.
2. Register stage 4 block projections if the article sections were edited separately,
   then create one stitch report and diff-pool for the assembled article.
3. Close the stage 4 pool and run `finalize-article`.
4. Run deterministic project checks for links, tables, diagrams and template-required
   sections.
5. Invoke `revmux` on the article diff using its standard workflow. Use
   `comprehensive` for the first substantive round.
6. Put accepted review findings into one article diff-pool. Every item names the exact
   `source_finding_id`; every critical/major finding must be covered.
7. Register each actionable round with `record-review --diff-pool`. Apply and verify
   only that pool through `resolve-review` and `verify-review`, then call
   `article-updated` and re-review with the profile selected by `revmux` rules.
8. A failed verification reopens the same item. A degraded round forms no diff-pool:
   restore the missing source and rerun it because partial silence is not evidence.
9. When state becomes `spec_ready`, record route `stop` or `delivery`.

**Exit:** One reader-facing article exists, standard revmux convergence has no gating
finding, sources are not degraded, and the next route is explicit.
