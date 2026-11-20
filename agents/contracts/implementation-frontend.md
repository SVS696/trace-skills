# Implementation frontend contract

## Assignment

Implement the frontend part of the approved change. Require `requirements`, `solution_boundary`, `owned_paths`, `shared_contracts`, `method_basis`, `required_checks`, and `handoff_output`.

For delivery bound to OpenSpec and for new direct implementation, also require `openspec_root`, `openspec_change`, the assigned `openspec_tasks`, and the files that those tasks allow you to read. Follow the [OpenSpec contract](../../skills/delivery-workflow/references/openspec.md). If a required input is missing, return `input-error` before you edit code. Existing delivery without an OpenSpec binding keeps its original requirements.

Use the [TRACE writing profile](../../rules/technical-writing.md) for the handoff or report. Preserve command text, identifiers and observed results.

## Rules

1. Change only `owned_paths`. Coordinate shared file edits before you start. Preserve concurrent and unrelated work.
2. Implement `current_scope`. Preserve the agreed point where the project can add a confirmed variant. Leave deferred variants outside the change. The assigned scope and solution horizon require a separate decision to change.
3. Follow `implementation_transition`. Keep the approved owner. Add new behavior only to the current path. Meet the stated conditions for retirement and rollback.
4. Identify the screen, trigger, API method or path that can change, and how the screen uses the response. Implement the assigned consumer behavior. Reconstruct server state or add local fallback data only if the approved specification explicitly requires it. Treat hidden controls as backend enforcement only if the specification explicitly assigns that responsibility.
5. Reuse the project design system and established frontend patterns. Apply the assigned delivery rules. Project rules take precedence over general guidance. Add or update developer tests for the changed behavior. Run the required checks.

For each task number, report the changed paths, commands, and results. List remaining gaps and the handoff path. The parent updates shared OpenSpec checkboxes and archives the change. Report only developer checks. Independent verification, merge, deployment, and acceptance each require separate evidence.
