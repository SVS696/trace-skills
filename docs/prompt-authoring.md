# Writing TRACE instructions

Apply this checklist when changing a skill, role contract, or template comment. It is
an authoring aid, not a new runtime gate or extra agent role.

- State the task, required inputs, allowed reads/writes and exact outputs separately.
- Give one ordered path. Remove conflicting old instructions instead of appending an
  exception that forces the model to choose. State prerequisites beside the action.
- Give explicit missing-input behavior and success criteria. Do not assume that a
  child role inherited the parent's project knowledge or authority.
- Keep facts, instructions, examples and variable inputs visibly separate. Use a small
  number of representative examples; examples must obey the actual contract.
- Say what to do and why. Keep prohibitions for real boundaries, not as a substitute
  for the expected action. Link the authoritative rule instead of copying it everywhere.
- Test the next concrete action and produced artifact on realistic ambiguous inputs;
  an old model result does not establish behavior for changed instructions.

Basis checked 2026-09-09:
[OpenAI Cookbook: GPT-5 prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide)
explains why contradictory or vague instructions impair precise instruction following.
[Anthropic: Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
emphasizes explicit outputs, sequential steps and representative examples.
[Anthropic: Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
recommends sufficient, bounded context, clear sections and narrowly defined tools.
The TRACE decisions above are a local application of these principles, not vendor
requirements for TRACE's particular state machine or document structure.
