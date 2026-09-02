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
`delivery-advance`. `caseflow.py status` is the source of truth on resume.

## Stage 1: Plan

**Entry:** Approved article and route=`delivery`.

1. Create bounded backend/frontend/test lanes with exact paths, requirements and tests.
2. Stitch lane plans for API contracts, sequencing, ownership and shared files.
3. Resolve one planning diff-pool before code changes.

**Exit:** Lanes are independently executable and their contracts compose.

## Stage 2: Build

**Entry:** Stage 1 pool closed.

1. Implement lanes with developer tests.
2. Integrate once, run build/tests, and collect all defects into one stage pool.
3. Apply only pooled corrections and repeat the same checks.

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
