# Smoke Break integration

Smoke Break measures elapsed time and prompts the agent to run `P23 COURSE-CHECK`. TRACE owns the verdict and the case state.

## Shared configuration

Set the interval in `~/.smoke-break.env`.

```dotenv
SMOKE_BREAK_INTERVAL_MS=900000
```

TRACE recommends 15 minutes. The upstream default is five minutes. The plugin reads the configuration when the next turn starts.

## Codex

Install the upstream plugin and check it.

```bash
codex plugin marketplace add ElKornacio/agent-plugins --ref 511e18062c95d746bed7ff0ca300fbcbd31fc57f
codex plugin add smoke-break@agent-plugins
python3 scripts/smoke_break_dependency.py verify --runtime codex
```

## Claude Code

The upstream plugin supplies a Codex manifest. For Claude Code, install the TRACE adapter. It uses the same `UserPromptSubmit` and `PostToolUse` events.

```bash
claude plugin marketplace add SVS696/trace-skills --scope user
claude plugin install smoke-break@trace-smoke-break --scope user
python3 scripts/smoke_break_dependency.py verify --runtime claude
```

The adapter keeps the existing Claude hooks. If the adapter fails, tool calls can continue. The adapter stores timestamps, the interval and a hash of the session ID in a per-user temporary directory with a limit on the number of state files.

## Verification

```bash
python3 scripts/smoke_break_dependency.py verify --runtime codex --runtime claude
```

Specify each runtime when you record an installation result. Without `--runtime`, the verifier checks each runtime whose CLI it finds. It reports a missing CLI, a missing or disabled plugin, a version or source mismatch, or an invalid reminder marker. If the verifier cannot read the install path or source revision, it reports `unverified`.

Start a new session after installation. If the interval expires during a long tool call or while the agent is idle, the hook can send the reminder after the next tool completes.
