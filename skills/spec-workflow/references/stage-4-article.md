# Stage 4: Article and review

**Entry:** A hybrid case has closed stage 3, or an article-first case opened directly at
stage `4`.

1. The article editor projects the latest block artifacts into the unchanged template.
   The public article contains no block-process ids, findings or internal state. If a
   requirement, scenario or AC still lacks a decision/evidence, return it as a blocking
   stage-4 diff item; do not publish a polished backlog of unknowns. For a multi-layer
   change, preserve the layer scopes, responsibility boundary, handoff contract,
   requirement owners and separate BE/FE/E2E evidence in the closest existing template
   sections; do not add a new template structure.
2. Register the stage 4 article projection and method basis. Dispatch two separate
   narrow runs on the exact submitted article bytes:
   - `quality-pass-reviewer` executes `simplicity-spec`;
   - a different `quality-pass-reviewer` run executes `humanizer` with the project
     style profile and bounded publication rules, including reader-version history.
   Both follow [quality-pass.md](../../../rules/quality-pass.md). Reading a `SKILL.md`, mentioning the
   gate, or returning an informal "looks clean" is not a pass.
3. Give the article and both reports to `spec-integration-editor`. It creates one stitch
   report and one diff-pool. Every reported finding is represented by its exact
   `source_finding_id`; simplicity and language changes are not hidden edits.
4. Register the stitch with `record-stitch --simplicity-report ... --humanizer-report
   ...`, apply only that pool, and verify both each exact change and the full finding
   class. A language change must preserve normative meaning and traceability.
5. Close the stage 4 pool, run `advance` to record `content_ready_at`, then run
   `finalize-article`. A blocking input may close only as `verified`, after its
   answer/evidence is present in the article; it cannot be waived. `record-review`
   rejects migrated or manually advanced cases without this readiness marker.
6. Run deterministic project checks for links, tables, diagrams and template-required
   sections. If they change the article, register the new fingerprint with
   `article-updated` before invoking review.
7. Invoke `revmux` on the article diff using its standard workflow. Use
   `comprehensive` for the first substantive round. Before every later round, count
   completed non-degraded rounds for the case. Five is a hard cap; a technical retry of
   a degraded or failed run does not count. Round six requires a new explicit user
   decision and must never be inferred from “fixes require confirmation”. Read
   `review_cycles_used` and `review_cycles_remaining` from `caseflow.py status` before
   preparing a round. `record-review` rejects a substantive round beyond the cap unless
   the exact user decision is supplied as `--cap-decision-ref`.
8. After a complete non-degraded result, send the exact receipt and only the evidence
   needed for its findings to a fresh `quality-pass-reviewer` run. It applies
   `simplicity-spec` with `purpose: revmux-finding-adjudication`: confirm the reported
   problem against the current requirement, reachable scenario and protected minimum,
   then propose the smallest sufficient correction. It must account for every finding
   as accepted or dismissed with evidence; it must not re-review the whole article.
   Revmux verification remains the factual check, while this pass prevents severity or
   model paranoia from becoming work automatically.
9. Triage the confirmed set using `P17`: record likelihood, impact and correction
   cost. Put every accepted correction into one article diff-pool; dismissed findings
   do not enter it. Every item names the exact `source_finding_id`.
10. The normalized receipt must use schema 1 and bind `article_sha256` to the current
   article; it also carries exact `sources.ids`, `sources.expected`,
   `sources.reported`, `sources.degraded`, `findings`, and `open_questions`.
   Every finding names the reviewer/lens ids that raised it. A later clean round must
   include every source behind a finding accepted into the previous diff-pool; changing
   to a narrower profile cannot silently close that finding class.
11. Register each round with `record-review --adjudication-report ... [--diff-pool ...]`.
   A healthy round with findings is rejected without the adjudication report; a diff
   is rejected unless it covers every accepted finding and none of the dismissed set.
   Apply and verify only that pool through `resolve-review` and `verify-review`;
   register any defect
   discovered during correction with `append-review-item`. Then call
   `article-updated` and re-review with the profile selected by `revmux` rules only
   while the cap and `P19` simplicity brake remain open.
12. A failed verification reopens the same item. A waived item is recorded with
   `waive-review --decision-ref`. A degraded round forms no diff-pool:
   restore the missing source and rerun it because partial silence is not evidence.
13. If revmux returns open questions, `record-review` moves to
    `revmux_decision_pending`. Present the questions to the user, then record the answer
    with `record-review-decisions --decision-ref <ref> [--diff-pool <pool>]`. When the
    same round also has gating findings, that pool must cover them and any accepted
    question-driven changes.
14. When state becomes `spec_ready`, record route `stop` or `delivery`; a delivery route
    also declares stable lane ids with repeated `--lane` arguments.

**Exit:** One substantively complete reader-facing article exists before the first
`revmux` call; review either converged without gating
findings or stopped at the cap with an explicit user disposition of residual risk;
sources in the relied-on round are not degraded, and the next route is explicit.
