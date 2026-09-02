---
name: delivery-workflow
description: >-
  Use when an approved specification explicitly routes to implementation and the
  change must be built through bounded lanes with repeated integration barriers.
  Not for requirements authoring, deployment without authorization, or formal acceptance.
allowed-tools: Read Glob Grep Write Edit Bash Task AskUserQuestion
---

# Delivery workflow

## Essential principles

Read [the process kernel](../../rules/process-kernel.md) once for the task. Use
`method-library` to materialize the lane's delivery basis from the preserved SWEBOK,
Software Engineering at Google and specialized standard distillates.

1. Start only from `spec_ready` with route `delivery`.
2. Lanes may work independently, but every stage ends in one integrated change.
3. All integration defects enter one exact stage diff-pool before correction.
4. Developer checks, independent verification, merge, deploy and acceptance remain
   separate evidence gates.
5. Load only the assigned lane, shared contract and current integration report.

## When to use

- Approved requirements are ready for backend, frontend or combined implementation.
- Several code lanes need bounded parallel work and explicit integration.
- A paused delivery case can resume from recorded artifacts.
- A completed implementation needs independent verification and handoff evidence.

## When not to use

- Requirements are incomplete: return to `spec-workflow`.
- The user chose to stop after the specification.
- The task is a tiny isolated edit with no lane interaction: implement directly.
- The request is only to deploy or change a tracker status: use that system's workflow.

## Four stages

Read [delivery-stages.md](references/delivery-stages.md) and execute only the current
stage reported by the case state.

Before assigning a lane, materialize `core-change` plus at most one applicable
specialized route such as `backend-http`, `backend-data`, `frontend-behavior`,
`accessibility`, `test-design`, `risk-security` or `review-static-analysis`. Pass only
that lane basis and its hash to the agent.

| Stage | Independent work | Integration barrier |
|---|---|---|
| 1. Plan | lane scope and tests | contracts, ordering and ownership |
| 2. Build | code and developer tests | integrated build and one defect pool |
| 3. Verify | independent evidence | full change, regressions and conformance |
| 4. Handoff | release/readiness artifacts | one bounded handoff report |

## Agents

- `implementation-backend` owns assigned backend files only.
- `implementation-frontend` owns assigned frontend files only.
- `implementation-verifier` is read-only except for test automation explicitly assigned.

## Success criteria

- Every code change traces to approved scope.
- Every stage diff-pool is closed with receipts.
- Integrated tests and project conformance checks pass.
- Independent verification is recorded separately from developer self-checks.
- Final report states what is implemented, committed, merged, deployed and accepted
  without collapsing those statuses.
