# Delivery stages

Initialize from `spec_ready` after the [OpenSpec preflight](openspec.md):

```bash
python3 scripts/caseflow.py route --case-root CASE --decision delivery \
  --lane BACKEND --lane FRONTEND --lane TEST \
  --openspec-root /absolute/planning-repo --openspec-change CHANGE
```

For every stage, submit one artifact and materialized method basis per declared lane
with `delivery-submit`, then use `delivery-open-stitch` and
`delivery-record-stitch`. Close the one stage pool only through `delivery-resolve`,
`delivery-verify --result pass|fail`, or `delivery-waive --decision-ref`; advance with
`delivery-advance`. A newly discovered defect is registered with
`delivery-append-item --item-file`, never by hand-editing the pool. `caseflow.py status`
is the source of truth on resume.

Before assigning or resuming one lane, obtain its bounded read-set with
`caseflow.py context --case-root CASE --lane BACKEND`. It contains the reviewed article,
the current recorded lane artifacts if any, and the previous delivery stage/stitch;
it never returns specification block drafts as the active delivery context.

## Stage 1: Plan

**Entry:** Approved article, bound OpenSpec package and route=`delivery`.

1. Map OpenSpec task numbers to bounded backend/frontend/test lanes with exact paths, requirements, accepted
   `solution_boundary` and tests.
   Carry its implementation transition into lane ownership: one authoritative path per
   stage, explicit superseded paths, retirement trigger and rollback where applicable.
2. Stitch lane plans for API contracts, sequencing, ownership and shared files. For
   every cross-layer guarantee, name its authoritative lane, consumer duty, data
   direction and separate BE/FE/E2E check.
   For several repositories identify all component SHAs, old/new provider-consumer
   compatibility where mixed versions are possible, joint build/environment,
   migrations/flags and merge/deployment order with rollback under the
   [handoff contract](../../../rules/handoff-contract.md).
3. Resolve one planning diff-pool before code changes.

**Exit:** Lanes are independently executable and their contracts compose.

## Stage 2: Build

**Entry:** Stage 1 pool closed.

1. Implement assigned OpenSpec tasks with developer tests. Return per-task evidence;
   the parent updates shared checkboxes after checking results.
2. Integrate once, run non-LLM build/tests and static checks, correct failures,
   then freeze one diff snapshot. A separate
   `quality-pass-reviewer` runs `simplicity-code` and writes the
   [observable report](../../../rules/quality-pass.md) bound to that
   snapshot and the exact skill bytes.
3. Repeat deterministic checks after corrections and before any model dispatch,
   then create one stage pool covering accepted simplicity findings
   and all remaining defects. Register it with `delivery-record-stitch
   --simplicity-report ...` and preserve the protected minimum.
4. Apply only pooled corrections and repeat the same checks. The handoff must show the
   simplicity result, including a clean line when nothing was removed.

**Exit:** One integrated change passes developer checks.

## Stage 3: Verify

**Entry:** Integrated developer checks pass.

1. Independent verifier traces approved article to the OpenSpec package, and its
   requirements/tasks to code and tests. Checked boxes alone are not evidence.
2. Run project conformance and risk-proportional regression checks. Verify provider
   enforcement directly, consumer behavior separately, then their E2E composition;
   do not let one contour stand in for another.
   For several repositories check the joint set of exact SHAs; independent green
   pipelines alone do not prove compatible behavior. A changed component requires
   affected joint checks on the new combination. If no joint build is available,
   keep integrated verification open. Analytical review and code review do not
   replace QA's executed behavioral checks on a stated build and environment.
3. If revmux is used, send its findings first to an independent `simplicity-code`
   adjudication (or `simplicity-spec` for a documentation subject), record accepted
   corrections in one pool and dismiss others with evidence. Apply only the pool,
   run deterministic checks and recheck the correction diff and affected classes
   with their required sources. Use the same five-round cap and minor-pending
   stopping rule as specification review; minor residuals never mean acceptance.
   Without revmux, put accepted defects into one verification pool and recheck
   the exact changed diff.

**Exit:** Independent evidence has no gating defect; developer and verifier receipts
remain distinct.

## Stage 4: Handoff

**Entry:** Stage 3 pool closed.

1. Record exact commit/MR/test evidence, OpenSpec change and task evidence, and unresolved gaps.
   Use the [handoff contract](../../../rules/handoff-contract.md) with recipient,
   authoritative versions, criterion-to-evidence coverage and conditions for the next
   action. Compare any deployed version with the checked set when deployment is in scope.
2. State merge, deploy and acceptance as independent current facts.
3. Perform external writes only when separately authorized and read them back.

**Exit:** A bounded handoff report exists; no status is inferred from another gate.
