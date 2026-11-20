# How to write TRACE instructions

Use these rules when you edit a skill, a role contract, or a comment in a template. Follow the writing profile for the language of the document. [Technical writing](../rules/technical-writing.md)

1. Name the task. List the required inputs, the files the agent can read or change, and the expected outputs.
2. Give the steps in execution order. Put each prerequisite beside the action it controls. When a rule changes, replace the old rule in its original location.
3. Tell the agent what to do if an input is missing. State how to check the result. A child agent needs its own project context and a clear description of its authority.
4. Label examples and variable input. Use examples that follow the same rules as a real case.
5. For a boundary, state the permitted action and the reason for the restriction. Link to the rule that owns the decision.
6. Test a realistic case with more than one possible interpretation. Check the next action and the resulting document against the source. A test result applies to the version that ran.

TRACE uses these checks during editing. The project reviewed the following sources on 2026-09-09. They describe how to write prompts and select context. TRACE defines its own stages and document formats. [OpenAI prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide) · [Anthropic prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) · [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
