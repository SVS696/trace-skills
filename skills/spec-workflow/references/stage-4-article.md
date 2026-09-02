# Stage 4: Article and review

**Entry:** Stage 3 diff-pool is closed and case stage is `4`.

1. The article editor projects the latest block artifacts into the unchanged template.
   The public article contains no block-process ids, findings or internal state.
2. Register a stage 4 projection and method basis for every block, then create one
   stitch report and diff-pool for the assembled article.
3. Run `simplicity-spec` on the solution expressed by the complete article before
   closing the stage 4 pool. Put every accepted `SIMPLIFY`, `REMOVE` or `DEFER` into
   that same pool, apply it, and preserve the protected minimum. Show the resulting
   simplicity table or clean line with the article result.
4. Close the stage 4 pool and run `finalize-article`.
5. Run deterministic project checks for links, tables, diagrams and template-required
   sections. If they change the article, register the new fingerprint with
   `article-updated` before invoking review.
6. Invoke `revmux` on the article diff using its standard workflow. Use
   `comprehensive` for the first substantive round. Before every later round, count
   completed non-degraded rounds for the case. Five is a hard cap; a technical retry of
   a degraded or failed run does not count. Round six requires a new explicit user
   decision and must never be inferred from “fixes require confirmation”. Read
   `review_cycles_used` and `review_cycles_remaining` from `caseflow.py status` before
   preparing a round. `record-review` rejects a substantive round beyond the cap unless
   the exact user decision is supplied as `--cap-decision-ref`.
7. Triage every finding before correction using `P17`: record reachability in the
   normal workflow, likelihood, impact and complexity cost. Severity alone does not
   make a finding actionable. Put accepted corrections and explicitly waived gating
   findings into one article diff-pool. Every item names the exact
   `source_finding_id`; every critical/major finding must be covered by one of those
   dispositions.
8. The normalized receipt must use schema 1 and bind `article_sha256` to the current
   article; it also carries exact `sources.expected`, `sources.reported`,
   `sources.degraded`, `findings`, and `open_questions`.
9. Register each actionable round with `record-review --diff-pool`. Apply and verify
   only that pool through `resolve-review` and `verify-review`; register any defect
   discovered during correction with `append-review-item`. Then call
   `article-updated` and re-review with the profile selected by `revmux` rules only
   while the cap and `P19` simplicity brake remain open.
10. A failed verification reopens the same item. A waived item is recorded with
   `waive-review --decision-ref`. A degraded round forms no diff-pool:
   restore the missing source and rerun it because partial silence is not evidence.
11. If revmux returns open questions, `record-review` moves to
    `revmux_decision_pending`. Present the questions to the user, then record the answer
    with `record-review-decisions --decision-ref <ref> [--diff-pool <pool>]`. When the
    same round also has gating findings, that pool must cover them and any accepted
    question-driven changes.
12. When state becomes `spec_ready`, record route `stop` or `delivery`; a delivery route
    also declares stable lane ids with repeated `--lane` arguments.

**Exit:** One reader-facing article exists; review either converged without gating
findings or stopped at the cap with an explicit user disposition of residual risk;
sources in the relied-on round are not degraded, and the next route is explicit.
