# Smoke Break integration

Smoke Break supplies the elapsed-time reminder that triggers `P23 COURSE-CHECK`.
It does not own the TRACE verdict and does not mutate case state.

## Shared configuration

Create `~/.smoke-break.env`:

```dotenv
SMOKE_BREAK_INTERVAL_MS=900000
```

Fifteen minutes is the TRACE recommendation. The upstream fallback remains five
minutes. Configuration is read at the start of the next turn.

## Codex

Use the upstream plugin:

```bash
codex plugin marketplace add ElKornacio/agent-plugins --ref 511e18062c95d746bed7ff0ca300fbcbd31fc57f
codex plugin add smoke-break@agent-plugins
python3 scripts/smoke_break_dependency.py verify --runtime codex
```

## Claude Code

Upstream currently ships a Codex manifest only. TRACE therefore includes a minimal
Claude Code adapter for the same `UserPromptSubmit` and `PostToolUse` events:

```bash
claude plugin marketplace add SVS696/trace-skills --scope user
claude plugin install smoke-break@trace-smoke-break --scope user
python3 scripts/smoke_break_dependency.py verify --runtime claude
```

The adapter is fail-open and stores only timestamps, the configured interval and a
hash of the Claude session id in a bounded per-user temporary directory. Existing
Claude hooks are not replaced.

## Verification

```bash
python3 scripts/smoke_break_dependency.py verify --runtime codex --runtime claude
```

Without `--runtime`, the verifier checks the runtimes whose CLI executables are present;
explicit flags are preferred in installation receipts. It distinguishes an absent CLI,
a missing plugin, a disabled plugin, version/source drift, a broken reminder marker and
`unverified`, when the install path or source revision cannot be read.
New sessions are required after plugin installation. Reminders cannot fire during one
long-running tool call or while the agent is idle; the checkpoint arrives after the
next observed tool completion.
