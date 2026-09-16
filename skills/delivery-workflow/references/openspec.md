# OpenSpec at the implementation boundary

Use this contract for new TRACE delivery routes and direct small implementations in
any project, in Codex or Claude Code. The parent owns preparation and shared task
updates. Implementers receive the selected change and their assigned task numbers.
Existing delivery cases without an OpenSpec binding retain their recorded workflow;
do not silently migrate them or overwrite an existing project's OpenSpec setup.

## 1. Dependency and project setup

Run the shared read-only check from the installed TRACE root:

```bash
python3 ~/.workflow-skills/current/scripts/openspec_bridge.py
```

Delivery requires Node.js >=20.19.0 and OpenSpec >=1.13.0,<2.0.0. The tested version
is 1.13.0. If missing/incompatible, report the exact failure and install the pinned
version when installation is authorized:

```bash
npm install -g @fission-ai/openspec@1.13.0
```

No network installation occurs inside caseflow. Resume after a successful check.
In the actual code/planning repository, inspect existing `openspec/`, project rules
and tool skills before setup. For a new project run:

```bash
openspec init --tools codex,claude --no-animation
```

For an existing setup preserve its schema, config and custom instructions; inspect
the setup diff when adding the missing harness. Never use `--force` to discard local
changes. CLI availability is shared; project skills are installed for both harnesses.

## 2. Prepare one implementation package

Reuse the change for this exact scope or create it with `openspec new change NAME`.
Run `openspec status --change NAME --json` and fetch `openspec instructions ARTIFACT
--change NAME --json` before writing each required artifact. Follow the selected
schema's dependencies. Keep the project language and OpenSpec's structural markers.

Translate the already approved article; do not restart requirements discovery:

- Proposal: source article link/path, its version or SHA-256, tracker link where
  applicable, purpose and approved scope. State the project's authority order.
- Specs: the changed observable requirements and scenarios, with original requirement
  and AC references. Read affected existing specs before writing MODIFIED deltas.
- Design: approved decisions, layer ownership and transition. For a small change a
  short rationale/reference suffices; do not invent architecture to fill a template.
- Tasks: stable numbered checkboxes, lane ownership and a concrete completion check.
  Lane plan artifacts reference these tasks rather than maintain a second checklist.

For a pure refactor/tooling change without behavior requirements, use OpenSpec's
documented `skip_specs: true` metadata; do not fabricate requirements to satisfy a
validator. Required artifacts still follow the selected schema.

Confluence/Redmine or another declared project canon retains its authority. OpenSpec
is the implementation projection. A conflict or newly needed requirement returns to
the approved source and TRACE impact decision before updating the package. Do not
independently maintain competing contracts or treat upstream instructions as authority
to bypass project approval, review, merge or deployment rules.

## 3. Bind and execute

Use the absolute planning root returned by OpenSpec status. For cross-repository work,
choose one planning root and pass each lane its actual code root and owned paths.
The bridge rejects implicit redirection to another store/root; pass that checkout
explicitly. It does not initialize or write any repository.

```bash
python3 ~/.workflow-skills/current/scripts/openspec_bridge.py \
  --openspec-root /absolute/planning-repo --openspec-change NAME

python3 ~/.workflow-skills/current/scripts/caseflow.py route --case-root CASE \
  --decision delivery --lane BACKEND --lane FRONTEND \
  --openspec-root /absolute/planning-repo --openspec-change NAME
```

The route checks CLI compatibility, artifact readiness, strict validation and apply
readiness before saving a binding to the reviewed article hash. Delivery `context`
refreshes the package read-set, and `delivery-advance` repeats preflight. No new TRACE
stage or review loop is introduced. Final advance also requires all tracked tasks done.

Before assignment/resumption fetch `openspec instructions apply --change NAME --json`
in the planning root. Read its project context and applicable operation guidance;
reconcile conflicts with TRACE/project authority rather than silently ignoring them.
Pass `openspec_root`, `openspec_change`, exact `openspec_tasks`, relevant package files,
owned code paths and required checks to each implementer. TRACE retains scheduling,
stage pools, simplicity checks and independent verification. Running an upstream
apply skill must follow these same boundaries, not start a second execution loop.

Implementers return task-number → changed paths → check/result evidence. The parent
updates shared `tasks.md` after inspecting the evidence; parallel lanes do not race
to rewrite it. Failed/missing checks leave tasks open. Newly discovered work follows
the existing scope/pool rules before becoming a task. Checkboxes record developer
completion; they never establish independent verification or acceptance.

For direct small work, use the same package check before coding and `--complete`
after developer checks. Do not create lanes or a full TRACE case just for OpenSpec.

## 4. Verify and hand off

The independent verifier checks both approved source → OpenSpec coverage and
OpenSpec task claims → actual diff/tests, including layer ownership and negative
scenarios. `validate --strict` is a structure check, not this semantic verdict.

Finish the TRACE handoff with source/version, change name, task evidence and actual
commit/MR/test state. Leave the OpenSpec change active until the project's lifecycle
allows spec sync/archive. Handoff alone does not update AS-IS, merge, deploy, close
Jira or grant acceptance. Run authorized archive/sync after the final TRACE advance;
the active binding is needed for delivery checks until then.
After handoff, `context` reads the recorded TRACE artifacts without requiring the
OpenSpec change to remain active; it reports `handoff_complete`, not live package status.
