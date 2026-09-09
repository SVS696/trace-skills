# Stage 4: Final article and revmux

Entry: stage 3 has an integrated article. Read only the selected project rules,
method basis, accepted solution boundary and bound architecture design when present.

## Prepare the article

1. Consolidate the whole article in the selected template variant. Resolve content
   gaps before review. Preserve owners, contracts, traceability and US/DoD lineage.
2. During authoring apply simplicity and language rules. Run deterministic checks
   for headings, links, tables, examples and actual diagram rendering. Correct the
   candidate directly. Neither authoring nor preflight creates a diff-pool.
3. Submit ARTICLE; open-stitch; register a ready integration report without a pool:
   record-stitch --report REPORT. The JSON report has schema: 1, stage: 4,
   status: ready, open_inputs: []. Advance, then finalize-article --article ARTICLE.
4. Prepare one ordinary revmux assignment on these article bytes. Include project
   logic/conformance, simplicity, reader language and triggered architecture criteria
   in this round's reviewer assignments. Bound architecture design is an input;
   its conformance reviewer must be independent from its author. Do not run a second
   standalone article-review process before or after revmux.

## Review and corrections

article → revmux → findings → diff-pool → fix → article v2 → ordinary revmux

1. Run the normal revmux workflow with the selected full review profile. Preserve
   relevant sources in later ordinary rounds; do not substitute targeted verification.
   Keep project review criteria in the profile and assignment scope in scope.md.
2. A complete result is a schema-1 receipt bound to article_sha256, with source ids,
   expected/reported counts, degraded sources, findings and open_questions. A degraded
   result creates no pool; restore the missing source and retry the ordinary round.
3. Apply simplicity-spec to the returned findings using a receipt-bound adjudication
   report. This is practical triage of those findings, not a second article review.
   Each finding is accepted with a minimal correction or dismissed with evidence.
4. Create one pool from the accepted findings. Each item names source_finding_id and
   targets the final article path plus the exact heading. List any intermediate
   artifact synchronization in the same correction; it never replaces the article fix.
5. Register record-review --receipt RECEIPT --adjudication-report REPORT --diff-pool POOL.
   For clean results no pool is needed. Resolve user questions before forming their
   corrections, using record-review-decisions and the actual decision reference.
6. Apply the complete correction batch to the final article and synchronize named
   supporting artifacts where needed. Run deterministic checks, then record each
   applied receipt with resolve-review. These receipts bind the resulting article
   bytes; writing only a block cannot satisfy them. Applied is not yet verified.
7. Call article-updated --article ARTICLE, then run the next ordinary revmux on the
   updated article. Do not call verify-review or launch a separate targeted check.
   A healthy clean round confirms the applied corrections. Remaining findings enter
   the next pool; the author never self-certifies semantic correctness.

Only revmux rounds consume the five-round limit. Deterministic authoring checks,
findings adjudication and failed/degraded technical retries do not consume it.
After round five ask for an explicit decision before another ordinary round. Stop
at clean results; if only minor findings remain, record --stop-at-minor without a
pool and show the residuals. Do not treat minor-pending as spec_ready.

Exit: article and honest review state. At spec_ready record route stop or the
explicitly authorized delivery route. Publication and acceptance remain separate.
