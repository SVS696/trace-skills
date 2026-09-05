---
name: spec-workflow
description: >-
  Use when starting, continuing, or reviewing a requirements specification that
  must start as one whole-template article and then deepen through semantic blocks
  with staged integration.
  Not for implementation work or migration of an existing Vigers case.
allowed-tools: Read Glob Grep Write Edit Bash Task AskUserQuestion
---

# Specification workflow

## Essential principles

Read [the process kernel](../../rules/process-kernel.md) once for the task. Before each
block submission, use `method-library` to materialize one applicable requirements route
into `method-basis/stage-NN-BLOCK.md`.

1. **Work from the whole to the parts.** Stage 1 fills the entire immutable template
   before focused block work begins. Blocks challenge and deepen a visible system model;
   they do not independently invent fragments that will be assembled later.
2. **Every stage ends with one integration barrier.** A focused block stage cannot
   advance before all contributions are reconciled into the whole article.
3. **Every detected defect enters one stage diff-pool.** Normal stage authoring produces
   the candidate projection; after the integration barrier, every corrective edit must
   name a `required-diff.json` item and produce a receipt.
4. **Load only the current read-set.** Use `caseflow.py context`; do not read all
   references, old drafts, agent contracts, or project documents at once.
5. **Review is not acceptance.** A green local check or revmux round does not prove
   publication, handoff, merge, deploy, or formal acceptance.
6. **A named skill is not an executed pass.** Stage 4 requires observable reports from
   separate `simplicity-spec` and `humanizer` runs bound to the submitted article.
7. **An owned gap is still a gap.** Every unresolved input is classified. If it can
   change requirements, scenarios or AC, it is a blocking item in the current stage
   diff until its answer/evidence is incorporated and verified.
8. **Separate layers without splitting the outcome.** When behavior crosses BE/FE or
   other technical surfaces, name one owner for every guarantee, the handoff contract
   and each surface's evidence. Do not create separate specifications merely by layer.
9. **Review findings are candidates, not work orders.** After a healthy `revmux`
   result, a separate narrow run applies `simplicity-spec` to the receipt findings.
   Only confirmed, material findings enter the correction diff.
10. **The accepted solution horizon travels with the case.** Every context contains the
    selected article's `solution_boundary`. Preserve its root capability, current scope
    and evidence-backed seam. A new variant or horizon change is a `P16` decision, not a
    block-level improvement.

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

**Entry:** Approved `decomposition-decision.json` and `execution-plan.json` exist, and
a case root exists or the user authorized its initialization.

1. For a new case, initialize it with `scripts/caseflow.py init`; it must consume the
   matching approved decision and plan plus the selected article entry.
2. Run `status`, then `context`.
3. If `context` reports a missing method basis, materialize it before assigning the
   block. Read only the stage file and paths returned in `read_set`.

**Exit:** The current stage, state, block list and bounded read-set are known.

### Phase 2: Execute exactly one stage

**Entry:** Phase 1 completed.

| Stage | Required reference | Output |
|---|---|---|
| 1 | [stage-1-foundation.md](references/stage-1-foundation.md) | whole-template baseline article |
| 2 | [stage-2-behavior.md](references/stage-2-behavior.md) | block depth plus integrated article projection |
| 3 | [stage-3-acceptance.md](references/stage-3-acceptance.md) | acceptance depth plus integrated article projection |
| 4 | [stage-4-article.md](references/stage-4-article.md) | consolidated article and revmux receipts |

Follow the selected stage file. Do not preload the other three.

Stages 1 and 4 use the reserved `ARTICLE` subject. Stages 2 and 3 use the semantic
blocks approved in preanalysis. Stage 2 and 3 stitches must write a new immutable
article projection instead of mutating the previous snapshot.

**Exit:** The stage has a stitch report and a registered `required-diff.json`; its
`deferred_inputs` register is present, and every content-blocking input is a diff item.

### Phase 3: Apply the pooled diff

**Entry:** Stage state is `remediation` or `ready`.

1. Read [diff-pool.md](references/diff-pool.md).
2. Apply only open items, preferably as one correction batch.
   For a `user-decision` item, the parent asks its exact question and uses the answer
   reference in the correction receipt. For `researchable` or `external-owner`, obtain
   the named evidence first. In every case, update the target artifact before verification.
3. If correction or verification reveals another defect, register it with
   `caseflow.py append-item --item-file`; never edit the fingerprinted pool manually.
4. Record one receipt per item with `caseflow.py resolve`.
5. Independently recheck each applied correction and record the result with
   `caseflow.py verify --result pass|fail`; the result is mandatory and never inferred.
6. Run `caseflow.py advance` only after every item is `verified` or `waived`.

**Exit:** The case advanced exactly one stage, or stopped with explicit unresolved items.

## Agents

Use only the role needed by the current assignment:

- `spec-evidence-analyst` for bounded source analysis;
- `spec-block-analyst` for one block at one stage;
- `spec-integration-editor` for stitch report and diff-pool;
- `spec-article-editor` for the stage 1 baseline and stage 4 consolidation;
- `quality-pass-reviewer` in one run for the full read-only `simplicity-spec` pass;
- `quality-pass-reviewer` in a different run for the full read-only `humanizer` and
  project reader pass.

The article editor receives the complete current article because its assignment is the
whole. A block analyst receives the previous article projection, its bounded sources and
its own method basis, not every source or every other block artifact.

## Success criteria

- The template was not changed.
- Stage 1 completed a full pass through the template before any semantic block submission.
- Stages 2 and 3 have every semantic block submission, one stitch, one new article
  projection and one diff-pool.
- Stage 4 has hash-bound observable `simplicity-spec` and `humanizer` reports from
  separate runs, and every finding is covered by the one stage diff-pool.
- Every applied item was separately verified; every waived item has a decision reference.
- No diff item carrying a blocking `input` was waived; every such item was verified.
- A multi-layer article identifies the owner and consumer of each shared guarantee,
  exact interface direction, and separate BE/FE/E2E acceptance evidence.
- `revmux` began only after the stage-4 article was substantively complete, not as a
  substitute for research or direct questions.
- Every non-degraded `revmux` result with findings has a receipt-bound
  `simplicity-spec` adjudication; its accepted set exactly matches the correction pool.
- The final article exists as one file and revmux is not degraded.
- The final route is explicitly `stop` or `delivery`.
- The final article implements the accepted solution boundary without publishing the
  internal horizon id or promoting deferred variants into current requirements.
