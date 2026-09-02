# Claude Code instructions

`AGENTS.md` is the canonical contributor instruction file for this repository. Read it
fully before changing workflow semantics.

User skills are installed through `scripts/install.py` into `~/.claude/skills`; narrow
Claude agents are copied from `agents/claude`. Do not load all skills, agent contracts
or method-library sources at once. Use the active skill, one stage/route and its exact
read-set.
