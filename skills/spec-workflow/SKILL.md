---
name: spec-workflow
description: >-
  Prepare or revise a specification after approved preanalysis. Start with the whole
  selected template, deepen it through semantic blocks, and review the final article
  through revmux. Not implementation, publication, or automatic legacy migration.
allowed-tools: Read Glob Grep Write Edit Bash Task AskUserQuestion
---
# Specification workflow

## Inputs and result

Read ../../rules/process-kernel.md once. Require the approved brief, decomposition,
plan, selected template, and exact article id. If an input is missing, name it; do
not infer approval. Use legacy-case-migration only for a requested legacy continuation.
A tiny wording correction does not need a new case.

The result is one reader-facing article. A ready specification is not publication,
implementation, handoff, or acceptance.
Analysis owns observable acceptance criteria. QA owns test cases, test data,
environment, regression and execution against the implementation. Review the article's
requirements and testability; product testing is not a prerequisite for article readiness.

## Context and authorship

1. Initialize with scripts/caseflow.py init, then read status and context.
2. Materialize one method-library route for the current assignment.
3. Build the complete assignment with context --project-rule PATH --source PATH
   (repeat as needed). Include applicable project rules and actual evidence files,
   not just a map linking to them. Resolve missing_required before dispatch.
4. Give the role this final read_set, one stage reference, exact output paths,
   accepted solution_boundary, and the relevant previous whole article.
5. Use the selected template variant under ../../rules/template-family.md. Preserve
   the source template; apply its section rules to the output article.

## Four authoring stages

| Stage | Reference | Output |
|---|---|---|
| 1 | references/stage-1-foundation.md | Whole article and US/DoD lineage |
| 2 | references/stage-2-behavior.md | Integrated behavioral article |
| 3 | references/stage-3-acceptance.md | Integrated acceptance article |
| 4 | references/stage-4-article.md | Final article, then ordinary revmux rounds |

Stages 1 and 4 use ARTICLE; stages 2 and 3 use the approved semantic blocks.
Each stage writes a new article snapshot. Authoring, integration and deterministic
preflight happen before review; they do not create correction pools.

Resolve missing evidence and product decisions during authorship. Return a direct
question for a missing decision; do not disguise it as prose or mark it ready.
Register a ready integration with record-stitch --report REPORT [--article ARTICLE],
without --diff-pool. The JSON report has schema: 1, stage: N, status: ready,
open_inputs: [], and describes the actual checks. Then advance.
Compatibility commands for old stage pools do not define the new workflow.

## One review loop

article → revmux → findings → diff-pool → fix → article v2 → ordinary revmux

Follow references/stage-4-article.md. Only accepted revmux findings create the
correction pool. Resolve each correction in the final article; an intermediate-file
edit alone is insufficient. Record applied receipts, call article-updated, then run
the next ordinary revmux. There is no separate targeted verification.

Revmux performs independent review, including applicable project, language,
simplicity and architecture criteria. Post-result simplicity adjudication selects
practical corrections; it does not run another article review. Count at most five
substantive revmux rounds. Stop early when clean or only minor residuals remain;
minor residuals are not a clean result. An extra round requires an actual user decision.

## Completion

Return the article, actual review state, residual findings or questions, and the
chosen stop/delivery route. Never upgrade a draft or applied fix to verified based
on the author's own assertion. Only the next healthy ordinary revmux can confirm it.
For transfer to Design, Dev or QA use the [handoff contract](../../rules/handoff-contract.md):
exact article version, accepted decisions, criteria, relevant risks and unresolved inputs.
