# Stage 1: Whole-template foundation

Entry: approved case inputs and selected template are available.

1. Assign spec-article-editor the whole template, bound brief, accepted solution
   boundary, final read_set, article_output and preanalysis_lineage_output.
2. Write articles/stage-01.md covering the whole applicable template. Show the
   end-to-end behavior, preliminary acceptance, and evidence gaps together.
3. Write preanalysis-lineage.json: each preliminary US/DoD appears exactly once as
   confirmed, changed, split or rejected, with final references and a reason.
4. Resolve content gaps through evidence or the user's decision before declaring
   the integration ready. The author corrects the candidate directly; no pool exists.
5. Submit ARTICLE, open-stitch, then have the integration editor check coherence,
   template applicability, lineage, ownership and the accepted solution boundary.
6. Register its JSON report with record-stitch --report REPORT (no diff-pool), then
   advance. Report schema: 1, stage: 1, status: ready, open_inputs: [].

Exit: one complete stage-1 article and lineage; unresolved content prevents advance.
This is authoring completion, not an independent review or acceptance.
