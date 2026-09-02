---
name: method-library
description: >-
  Use to select and materialize a small, source-traceable requirements or delivery
  method basis from the preserved Vigers, SWEBOK, Software Engineering at Google,
  ISTQB, RFC, WCAG and OWASP rule library. Not for reading the whole library or
  making product decisions.
allowed-tools: Read Glob Grep Write Bash
---

# Method library

## Purpose

Preserve the original book-derived rules without loading the whole corpus into a
model. The library contains exact mirrored distillates; this skill emits one bounded
`method-basis.md` for a specification block or delivery lane.

## Workflow

1. Read `rules/process-kernel.md` once in the parent task.
2. Inspect available routes:

   ```bash
   python3 scripts/rule_library.py list --domain requirements
   python3 scripts/rule_library.py list --domain delivery
   ```

3. Ask the deterministic router for a candidate:

   ```bash
   python3 scripts/rule_library.py route --domain requirements --task "<bounded assignment>"
   ```

4. Confirm the route against the assignment. The signal match recommends; it does not
   decide scope or requirements.
   `library/route-overrides.json` is the auditable overlay that extends pinned route
   maps without editing their mirrored content.
   Common exact ids needed before materialization are:

   - `requirements/scenarios` for actor, trigger, main flow, alternatives and exceptions;
   - `delivery/core-change` for every code change;
   - `delivery/backend-http` as the one specialized route for an HTTP endpoint,
     request/response or status-code surface.

   Use `list` for all other route ids; do not infer an id from prose.
5. Materialize one route. A second route is allowed only for an independent surface:

   ```bash
   python3 scripts/rule_library.py materialize \
     --domain requirements --route scenarios --output <method-basis.md>
   ```

6. Give the agent the generated basis path and hash. Do not give it the full source
   library or another block/lane basis.

## Boundaries

- Project instructions and current facts outrank the general method.
- A method rule is a question/checking lens, not invented product scope.
- Full Vigers `book-extract.md` is fallback-only at the pinned old commit.
- Source registry versions do not prove conformance beyond the checked surface.
- Run `python3 scripts/rule_library.py validate` before release or installation.
- The release count gate is exactly 70 native requirements rules and 30 native
  delivery rules. `tests/test_rule_library.py` pins these counts; `validate` separately
  checks mirror hashes, route references and reachability.

## Success criteria

- Every native `C/T/D` and `E/B/F/T/S` rule is reachable by at least one route.
- Mirrored files match their pinned SHA-256.
- The assignment loads no unselected method section.
