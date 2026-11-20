# TRACE contributor instructions

Use these rules when you change TRACE in Codex or another agent.

1. Before you change workflow behavior, read `README.md`, `docs/architecture.md`, and `rules/process-kernel.md`.
2. Change an article template only when the task includes that template.
3. The files in `library/manifest.json` are copies of specific source versions. To update a copy, select an explicit source commit. Update the source record and its SHA-256 in the same change.
4. Keep each native `C/T/D` and `E/B/F/T/S` rule reachable through a route. To add route coverage, edit `library/route-overrides.json`.
5. Add a workflow step only when a recurring defect requires it. First try a check within the existing stage.
6. Record proposed decisions, external writes, merges, deployments, and acceptance as separate events.
7. Before handoff, run these commands from the repository root:

   ```bash
   python3 -m unittest discover -s tests -v
   python3 scripts/rule_library.py validate
   python3 scripts/install.py verify
   ```

8. Keep `vigers` and `delivery-engineering` out of active skill discovery. See `legacy/preserved-sources.md` for their source versions and archive locations.
9. When you edit skills, agent contracts, or template comments, follow `docs/prompt-authoring.md` and `rules/technical-writing.md`. Specify the inputs, output, execution order, and allowed context. Check examples against the rule they illustrate.
