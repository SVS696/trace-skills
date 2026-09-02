---
name: process-timer
description: >-
  Use when recording start, pause, resume, readiness, handoff, stop, or activity
  events for a specification or delivery case and exporting a Work Metrics source.
  Not for estimating effort or deciding process state.
allowed-tools: Read Write Edit Bash
---

# Process timer

The timer records observed events only. It does not own stage gates, estimates,
review status or acceptance.

## Workflow

### Phase 1: Initialize

**Entry:** A stable work item id and source id are known.

Run `scripts/work_timer.py init`, then record `work_started`.

**Exit:** A ledger exists with an append-only event list.

### Phase 2: Record

**Entry:** Ledger validation passes.

- Use `pulse` for observed activity.
- Use `mark pause_started|deferred|resume` for explicit lifecycle changes.
- Use `ready_for_handoff` when the result is ready, not when it is accepted.
- Use `handoff` only after actual transfer.
- Use terminal stop states exactly as observed.

**Exit:** Every event has a stable id and timestamp; invalid transitions fail closed.

### Phase 3: Export

**Entry:** At least `work_started` exists.

Run `export-source`. Insert the returned source into a Work Metrics bundle whose
calendar and coverage declaration remain project-owned.

**Exit:** `work_metrics.py validate` accepts the complete project bundle.

## Non-negotiables

- Never infer activity during silence.
- Never turn a user stop into a pause or automatic resume.
- Never treat `ready_for_handoff` as `handoff`.
- Never invent a business calendar in this adapter.
