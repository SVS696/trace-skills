# Stage 3: Acceptance model

Entry: stage 2 has an immutable integrated article.

1. Each block proposes observable AC and acceptance-readiness DoD against the article.
   Keep the actor, entry condition, action and expected result concrete.
2. The integration editor incorporates these contributions into articles/stage-03.md.
   Resolve duplicated criteria, missing evidence and cross-block contradictions.
3. Check provider guarantees in BE/API, consumer behavior in FE/UI and composition
   in E2E. A passing check in one contour does not establish another contour.
4. Resolve missing content before readiness. Run deterministic authoring checks;
   correct the candidate directly, without a correction pool or verification loop.
5. Register schema: 1, stage: 3, status: ready, open_inputs: [] with record-stitch
   --report REPORT --article articles/stage-03.md; advance.

Exit: the article has observable acceptance for its requirements. Developer checks
are not product AC or DoD unless an actual normative requirement makes them so.
