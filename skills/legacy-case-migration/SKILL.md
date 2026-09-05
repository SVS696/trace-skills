---
name: legacy-case-migration
description: >-
  Use when an unfinished Vigers, Delivery Engineering, pre-article-led TRACE, or related
  legacy case must be reviewed and re-baselined without treating old process state as approval.
  Not for new cases or automatic bulk conversion.
allowed-tools: Read Glob Grep Write Bash
---

# Legacy case migration

Read [the process kernel](../../rules/process-kernel.md). Preserve subject matter and
applicable method rule IDs; do not preserve old state-machine verdicts. Use
`method-library` during the new preanalysis instead of reopening the full Vigers corpus.

## Principles

1. Preserve the old case and its Git history; migration creates a new assessment.
2. Carry forward verified subject matter, not old process verdicts or state-machine flags.
3. Re-evaluate the current article and evidence against the article-led four-stage model.
4. Prepare a post; do not send messages or change external systems without authorization.

## Workflow

### Phase 1: Inventory

**Entry:** Exact old case root is known.

1. Read its current status, article/draft, source index and unresolved findings.
2. Classify each artifact as `carry`, `recheck`, `obsolete`, or `unknown`.
3. Do not replay old agents or validators.

**Exit:** A read-only inventory identifies the latest trusted subject matter.

### Phase 2: Re-baseline

**Entry:** Inventory completed.

1. Run `spec-preanalysis` against the current subject and carried evidence.
2. Rebuild the current schema-3 brief: source queries/results/freshness and coverage,
   problem, goal, solution hypothesis, preliminary user stories and DoD, solution
   boundary plus implementation transition, architecture gate, scope, classified
   unknowns, dependencies and estimate. Do not copy legacy
   `unknown` strings unchanged: research them, turn them into direct user questions,
   name the external evidence owner, or prove they are implementation-only.
3. Decide whether the subject needs one specification or several, then define semantic
   depth blocks for each article-led case.
4. Create the schema-2 execution plan bound to the brief hash, with source refs and exit
   criteria. External plan synchronization remains optional and
   requires separate authorization plus read-back.
5. Start each specification case at stage 1. If a trustworthy full article already
   exists, submit it as the candidate whole-template baseline; do not skip directly to
   block stages merely because legacy block artifacts exist.
   Bind the rebuilt brief through `caseflow init --brief`; stage 1 must record the final
   disposition of every preliminary US/DoD.
6. Create a migration diff listing missing or stale material. Every still-open input
   that can change requirements, scenarios or AC is a blocking item assigned to the
   earliest applicable new stage; an owner label does not make it non-blocking.

**Exit:** The proposed stage-1 baseline and exact carry-forward set are explicit.

### Phase 3: Prepare post

**Entry:** Re-baseline completed.

Use [post-template.md](references/post-template.md). State that old review status does
not transfer automatically. Run the work-style `humanizer` pass before delivery.

**Exit:** A ready-to-send post exists; it has not been sent.

## Success criteria

- No old artifact was overwritten.
- No old PASS was presented as current acceptance.
- The preanalysis decision precedes the proposed stage-1 baseline.
- The new case binds current brief/decision/plan schemas; old artifacts are evidence,
  not substitutes for those contracts.
- The stage-1 baseline has evidence-based entry criteria and covers the whole template.
- Direct user questions have been asked before claiming their affected entry criteria;
  unanswered content questions remain blocking diff items, never harmless backlog.
- The post names what is carried, rechecked and intentionally not carried.
