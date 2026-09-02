# Stage 4: Article and review

**Entry:** Stage 3 diff-pool is closed and case stage is `4`.

1. The article editor projects the latest block artifacts into the unchanged template.
   The public article contains no block-process ids, findings or internal state.
2. Register a stage 4 projection and method basis for every block, then create one
   stitch report and diff-pool for the assembled article.
3. Close the stage 4 pool and run `finalize-article`.
4. Run deterministic project checks for links, tables, diagrams and template-required
   sections.
5. Invoke `revmux` on the article diff using its standard workflow. Use
   `comprehensive` for the first substantive round.
6. Put accepted review findings into one article diff-pool. Every item names the exact
   `source_finding_id`; every critical/major finding must be covered.
7. The normalized receipt must use schema 1 and bind `article_sha256` to the current
   article; it also carries exact `sources.expected`, `sources.reported`,
   `sources.degraded`, `findings`, and `open_questions`.
8. Register each actionable round with `record-review --diff-pool`. Apply and verify
   only that pool through `resolve-review` and `verify-review`, then call
   `article-updated` and re-review with the profile selected by `revmux` rules.
9. A failed verification reopens the same item. A waived item is recorded with
   `waive-review --decision-ref`. A degraded round forms no diff-pool:
   restore the missing source and rerun it because partial silence is not evidence.
10. If revmux returns open questions, `record-review` moves to
    `revmux_decision_pending`. Present the questions to the user, then record the answer
    with `record-review-decisions --decision-ref <ref> [--diff-pool <pool>]`. When the
    same round also has gating findings, that pool must cover them and any accepted
    question-driven changes.
11. When state becomes `spec_ready`, record route `stop` or `delivery`; a delivery route
    also declares stable lane ids with repeated `--lane` arguments.

**Exit:** One reader-facing article exists, standard revmux convergence has no gating
finding, sources are not degraded, and the next route is explicit.
