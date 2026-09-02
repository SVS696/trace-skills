---
name: spec-workflow
description: >-
  Use when starting, continuing, or reviewing a requirements specification that
  must produce one article from several semantic blocks with staged integration.
  Not for implementation work or migration of an existing Vigers case.
allowed-tools: Read Glob Grep Write Edit Bash Task AskUserQuestion
---

# Specification workflow

## Essential principles

Read [the process kernel](../../rules/process-kernel.md) once for the task. Before each
block submission, use `method-library` to materialize one applicable requirements route
into `method-basis/stage-NN-BLOCK.md`.

1. **The article template is the immutable spine.** Blocks are working views mapped
   to template sections, not separate deliverables. This prevents local completeness
   from replacing reader coherence.
2. **Every stage ends with one integration barrier.** No block enters the next stage
   before all blocks are stitched against each other.
3. **Every defect enters one stage diff-pool.** Do not make hidden improvements.
   Every edit must name a `required-diff.json` item and produce a receipt.
4. **Load only the current read-set.** Use `caseflow.py context`; do not read all
   references, old drafts, agent contracts, or project documents at once.
5. **Review is not acceptance.** A green local check or revmux round does not prove
   publication, handoff, merge, deploy, or formal acceptance.

## When to use

- A new analytical task needs one reader-facing specification.
- Several semantic blocks can be researched or drafted independently.
- An existing article needs a substantial staged rewrite.
- A case must resume from a recorded stage without replaying its full history.

## When not to use

- Migrating a Vigers case: use `legacy-case-migration` first.
- Implementing approved requirements: use `delivery-workflow` after route=`delivery`.
- Making a tiny local wording correction: edit and verify it directly.
- Reviewing an already assembled article only: invoke `revmux` directly.

## Workflow

### Phase 1: Resolve current state

**Entry:** An approved `decomposition-decision.json` exists and a case root exists or
the user authorized its initialization.

1. For a new case, initialize it with `scripts/caseflow.py init`; it must consume the
   approved article entry from the decomposition decision.
2. Run `status`, then `context`.
3. If `context` reports a missing method basis, materialize it before assigning the
   block. Read only the stage file and paths returned in `read_set`.

**Exit:** The current stage, state, block list and bounded read-set are known.

### Phase 2: Execute exactly one stage

**Entry:** Phase 1 completed.

| Stage | Required reference | Output |
|---|---|---|
| 1 | [stage-1-foundation.md](references/stage-1-foundation.md) | evidence, goal and boundaries |
| 2 | [stage-2-behavior.md](references/stage-2-behavior.md) | scenarios, rules, data and interfaces |
| 3 | [stage-3-acceptance.md](references/stage-3-acceptance.md) | AC, DoD and traceability |
| 4 | [stage-4-article.md](references/stage-4-article.md) | one article and revmux receipts |

Follow the selected stage file. Do not preload the other three.

**Exit:** The stage has a stitch report and a registered `required-diff.json`.

### Phase 3: Apply the pooled diff

**Entry:** Stage state is `remediation` or `ready`.

1. Read [diff-pool.md](references/diff-pool.md).
2. Apply only open items, preferably as one correction batch.
3. Record one receipt per item with `caseflow.py resolve`.
4. Independently recheck each applied correction and record the result with
   `caseflow.py verify`.
5. Run `caseflow.py advance` only after every item is `verified` or `waived`.

**Exit:** The case advanced exactly one stage, or stopped with explicit unresolved items.

## Agents

Use only the role needed by the current assignment:

- `spec-evidence-analyst` for bounded source analysis;
- `spec-block-analyst` for one block at one stage;
- `spec-integration-editor` for stitch report and diff-pool;
- `spec-article-editor` for stage 4 article projection.

Never give an agent the whole case when one block plus the previous stitch is enough.

## Success criteria

- The template was not changed.
- Each completed stage has every block submission, one stitch and one diff-pool.
- Every applied item was separately verified; every waived item has a decision reference.
- The final article exists as one file and revmux is not degraded.
- The final route is explicitly `stop` or `delivery`.
