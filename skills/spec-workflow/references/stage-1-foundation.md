# Stage 1: Foundation

**Entry:** Case stage is `1` and the template plus block map are fixed.

1. Give each block analyst only its source subset, template section mapping and case goal.
2. Each block writes `stage-01.md` with facts, source links, unknowns, exclusions and
   dependencies on other blocks. Do not write AC or implementation.
3. Register every artifact with `caseflow.py submit-block`.
4. After all submissions, run `open-stitch`.
5. The integration editor compares goals, terms, actors, boundaries and dependencies.
6. Write one stitch report and one stage `required-diff.json`; register both with
   `record-stitch`.

**Exit:** All block foundations agree on goal, scope, vocabulary and dependency edges,
or every disagreement is an open diff item.
