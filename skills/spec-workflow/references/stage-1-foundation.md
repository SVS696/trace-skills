# Stage 1: Whole-template baseline

**Entry:** Case stage is `1`; the template, article boundary and preliminary evidence
are fixed.

1. Give `spec-article-editor` the unchanged template, accepted `solution_boundary`,
   approved preanalysis artifacts, source index, bounded evidence and the stage-1
   method basis.
2. Write one complete working article at `articles/stage-01.md`. Walk every template
   section. State the current end-to-end model, requirements, scenarios, boundaries,
   data/interfaces and preliminary acceptance where evidence supports them. Mark a
   section explicitly not applicable only with a reason.
3. Write `preanalysis-lineage.json`. Account exactly once for every preliminary US and
   preliminary DoD from the bound brief as `confirmed`, `changed`, `split` or `rejected`;
   name final US/DoD refs and the reason. A rejected item has no final refs, confirmed
   and changed have one, split has at least two.
4. Do not disguise missing product decisions as polished prose. Surface every gap that
   can change requirements, scenarios or AC.
5. Register the article as reserved block `ARTICLE`, then run `open-stitch`.
6. The integration editor checks template coverage, one coherent vocabulary, actors,
   scope, causal chain, conformance to the accepted solution boundary and visible
   cross-layer ownership across the whole draft.
7. Write one gate report and one stage `required-diff.json`; register them with
   `record-stitch`. It reads the standard `preanalysis-lineage.json` from the case root.
   The ARTICLE submission is the stage article projection. `caseflow` verifies brief
   hash and exact PUS/DoD coverage.

**Exit:** A complete article-shaped system model exists before block work. Every template
section is populated or justified, and every content-blocking input has been incorporated
and verified. Every preliminary US/DoD has an explicit final disposition. Only
implementation-only or non-contract external readiness may remain deferred.
