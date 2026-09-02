---
name: legacy-case-migration
description: >-
  Use when an unfinished Vigers or Delivery Engineering case must be reviewed and
  re-baselined for the new workflow without treating old process state as approval.
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
3. Re-evaluate the current article and evidence against the new four-stage model.
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
2. Rebuild the brief: sources, problem, goal, solution hypothesis, preliminary user
   stories, scope, unknowns, dependencies and estimate.
3. Decide whether the subject needs one specification or several, and whether each
   resulting article uses `article-first` or `hybrid` assembly.
4. Create the execution plan. External plan synchronization remains optional and
   requires separate authorization plus read-back.
5. Only after preanalysis, map each approved article into the unchanged template and
   choose the earliest new stage whose entry criteria are actually satisfied.
6. Create a migration diff listing missing or stale material.

**Exit:** The proposed new case start stage and exact carry-forward set are explicit.

### Phase 3: Prepare post

**Entry:** Re-baseline completed.

Use [post-template.md](references/post-template.md). State that old review status does
not transfer automatically. Run the work-style `humanizer` pass before delivery.

**Exit:** A ready-to-send post exists; it has not been sent.

## Success criteria

- No old artifact was overwritten.
- No old PASS was presented as current acceptance.
- The preanalysis decision precedes any proposed new start stage.
- The new start stage has evidence-based entry criteria.
- The post names what is carried, rechecked and intentionally not carried.
