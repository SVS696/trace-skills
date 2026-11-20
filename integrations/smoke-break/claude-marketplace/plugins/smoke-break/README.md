# Smoke Break for Claude Code

This TRACE adapter runs the [Smoke Break plugin for Codex](https://github.com/ElKornacio/agent-plugins/tree/511e18062c95d746bed7ff0ca300fbcbd31fc57f/plugins/smoke-break) reminder in Claude Code.

Claude Code starts a separate process for each `UserPromptSubmit` and `PostToolUse` command hook. The adapter keeps turn state in a per-user temporary directory with a limit on the number of state files. Both plugins can read the same interval from `~/.smoke-break.env`.

```dotenv
SMOKE_BREAK_INTERVAL_MS=900000
```

The adapter stores only timestamps, the interval, and a hash of the Claude session ID. If the hook fails, tool calls can continue. A reminder needs a tool completion event. If the interval expires during a tool call or while the agent is idle, the adapter waits for the next such event.
