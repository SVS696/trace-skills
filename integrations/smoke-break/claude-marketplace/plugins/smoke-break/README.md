# Smoke Break for Claude Code

This is the TRACE-compatible Claude Code adapter for the upstream
[ElKornacio Smoke Break](https://github.com/ElKornacio/agent-plugins/tree/511e18062c95d746bed7ff0ca300fbcbd31fc57f/plugins/smoke-break)
Codex plugin.

It uses Claude Code `UserPromptSubmit` and `PostToolUse` command hooks. Turn state is
stored in a bounded per-user temporary directory because Claude Code command hooks are
separate processes. The shared `~/.smoke-break.env` configuration is compatible with
the upstream plugin:

```dotenv
SMOKE_BREAK_INTERVAL_MS=900000
```

The hook fails open. It never blocks a tool call, and its temporary state contains only
timestamps, the selected interval and a hash of the Claude session id. The reminder is
event-driven and cannot fire during one long-running tool call or while the agent is idle.
