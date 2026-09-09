# TRACE contributor instructions

These instructions apply to Codex and other repository agents.

1. Read `README.md`, `docs/architecture.md` and `rules/process-kernel.md` before a
   semantic workflow change.
2. Do not edit the article template as a side effect of process work.
3. Files listed in `library/manifest.json` are pinned mirrors. Update them only from an
   explicit source commit and update provenance plus SHA-256 in the same change.
4. Every native `C/T/D` and `E/B/F/T/S` rule must remain reachable through a route.
   Add missing coverage through `library/route-overrides.json`; never edit a pinned
   knowledge map merely to add local routing.
5. Add workflow complexity only for a demonstrated recurring defect. Prefer a check
   inside an existing stage over another stage or state.
6. Keep proposed decisions, external writes, merge, deploy and acceptance separate.
7. Before handoff run:

   ```bash
   python3 -m unittest discover -s tests -v
   python3 scripts/rule_library.py validate
   python3 scripts/install.py verify
   ```

8. Do not restore `vigers` or `delivery-engineering` to active discovery. Their pinned
   history and local archive locations are recorded in `legacy/preserved-sources.md`.
9. When changing skills, agent contracts or template comments, use
   `docs/prompt-authoring.md`: explicit inputs/outputs, one execution order, bounded
   context, and examples consistent with the rules. This is authoring guidance,
   not another runtime gate.
