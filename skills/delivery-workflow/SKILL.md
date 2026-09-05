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

1. Start by routing a `spec_ready` case to `delivery` with its stable lane ids.
2. Lanes may work independently, but every stage ends in one integrated change.
3. All integration defects enter one exact stage diff-pool before correction.
4. Developer checks, independent verification, merge, deploy and acceptance remain
   separate evidence gates.
5. Load only the assigned lane, shared contract and current integration report.
6. A separate `quality-pass-reviewer` run executes the full `simplicity-code`
   contract on the integrated implementation before independent verification. Its
   hash-bound findings enter the current exact diff-pool; reading the skill or naming
   the gate is not evidence.
7. Every shared guarantee keeps the layer owner declared by the specification. A FE
   guard does not replace BE enforcement; a BE test does not close FE behavior or E2E.
8. If `revmux` reviews an implementation diff, its findings are candidates until a
   receipt-bound narrow run applies `simplicity-code` to their real execution paths.
   Only confirmed findings enter a correction pool; speculative or unreachable cases
   remain dismissed evidence, not implementation work.
9. Every lane receives the accepted `solution_boundary` from case context. Implement
   current scope and preserve its justified seam, but do not add deferred variants or
   redesign the horizon. Follow its implementation transition and retirement/rollback
   conditions; new evidence returns to an explicit `P16` decision.

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

Read [delivery-stages.md](references/delivery-stages.md) and execute only
`delivery_stage` and `delivery_state` reported by `caseflow.py status`.

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
- `quality-pass-reviewer` is read-only and owns only the assigned observable
  `simplicity-code` report for one integrated diff.

## Success criteria

- Every code change traces to approved scope.
- The implementation conforms to the accepted solution horizon; a narrow hardcode and
  a speculative generic mechanism are both defects when they contradict its evidence.
- The approved transition has one authoritative path per stage; no superseded path
  gained behavior and retirement/rollback evidence is explicit where required.
- Backend, frontend and shared-contract changes remain inside their declared ownership;
  each layer is verified in its own contour before E2E composition is claimed.
- Every stage diff-pool is closed with receipts.
- Integrated tests and project conformance checks pass.
- The integrated implementation passed `simplicity-code`; removed/deferred complexity
  and the resulting runnable check are recorded in the build-stage evidence.
- Any `revmux` code findings were screened with `simplicity-code` before correction.
- Independent verification is recorded separately from developer self-checks.
- Final report states what is implemented, committed, merged, deployed and accepted
  without collapsing those statuses.
