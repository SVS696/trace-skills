# Delivery stages

Initialize from `spec_ready`:

```bash
python3 scripts/caseflow.py route --case-root CASE --decision delivery \
  --lane BACKEND --lane FRONTEND --lane TEST
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

**Entry:** Approved article and route=`delivery`.

1. Create bounded backend/frontend/test lanes with exact paths, requirements and tests.
2. Stitch lane plans for API contracts, sequencing, ownership and shared files.
3. Resolve one planning diff-pool before code changes.

**Exit:** Lanes are independently executable and their contracts compose.

## Stage 2: Build

**Entry:** Stage 1 pool closed.

1. Implement lanes with developer tests.
2. Integrate once, then run `simplicity-code` against the whole changed implementation.
   Classify every smell as `KEEP/SIMPLIFY/REMOVE/DEFER/ASK`; put accepted code changes
   into the same stage 2 diff-pool and preserve the protected minimum.
3. Run build/tests and collect all remaining defects into that one stage pool.
4. Apply only pooled corrections and repeat the same checks. The handoff must show the
   simplicity result, including a clean line when nothing was removed.

**Exit:** One integrated change passes developer checks.

## Stage 3: Verify

**Entry:** Integrated developer checks pass.

1. Independent verifier traces requirements to code and tests.
2. Run project conformance and risk-proportional regression checks.
3. Put accepted defects into one verification pool and recheck the exact changed diff.

**Exit:** Independent evidence has no gating defect; developer and verifier receipts
remain distinct.

## Stage 4: Handoff

**Entry:** Stage 3 pool closed.

1. Record exact commit/MR/test evidence and unresolved gaps.
2. State merge, deploy and acceptance as independent current facts.
3. Perform external writes only when separately authorized and read them back.

**Exit:** A bounded handoff report exists; no status is inferred from another gate.
