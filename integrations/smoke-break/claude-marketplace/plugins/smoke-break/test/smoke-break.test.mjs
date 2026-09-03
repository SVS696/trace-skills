import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { handleEvent, readInterval } from "../hooks/smoke-break.mjs";

function setup(t, intervalMs = 900_000) {
  const root = mkdtempSync(join(tmpdir(), "trace-smoke-break-test-"));
  const config = join(root, "config.env");
  const state = join(root, "state");
  writeFileSync(config, `SMOKE_BREAK_INTERVAL_MS=${intervalMs}\n`, "utf8");
  t.after(() => rmSync(root, { recursive: true, force: true }));
  return {
    env: {
      SMOKE_BREAK_CONFIG_FILE: config,
      SMOKE_BREAK_STATE_DIR: state,
    },
  };
}

test("reminds once per elapsed interval bucket", (t) => {
  const { env } = setup(t);
  handleEvent({ hook_event_name: "UserPromptSubmit", session_id: "s1" }, { now: 0, env });
  assert.deepEqual(
    handleEvent({ hook_event_name: "PostToolUse", session_id: "s1" }, { now: 899_999, env }),
    {},
  );
  const first = handleEvent(
    { hook_event_name: "PostToolUse", session_id: "s1" },
    { now: 900_000, env },
  );
  assert.equal(first.hookSpecificOutput.hookEventName, "PostToolUse");
  assert.match(first.hookSpecificOutput.additionalContext, /^Smoke break:/);
  assert.match(first.hookSpecificOutput.additionalContext, /about 15 minutes/);
  assert.deepEqual(
    handleEvent({ hook_event_name: "PostToolUse", session_id: "s1" }, { now: 900_001, env }),
    {},
  );
});

test("a new user prompt resets the timer", (t) => {
  const { env } = setup(t);
  handleEvent({ hook_event_name: "UserPromptSubmit", session_id: "s1" }, { now: 0, env });
  handleEvent({ hook_event_name: "UserPromptSubmit", session_id: "s1" }, { now: 800_000, env });
  assert.deepEqual(
    handleEvent({ hook_event_name: "PostToolUse", session_id: "s1" }, { now: 900_000, env }),
    {},
  );
});

test("reports actual elapsed time instead of the last interval boundary", (t) => {
  const { env } = setup(t);
  handleEvent({ hook_event_name: "UserPromptSubmit", session_id: "s1" }, { now: 0, env });
  const reminder = handleEvent(
    { hook_event_name: "PostToolUse", session_id: "s1" },
    { now: 2_400_000, env },
  );
  assert.match(reminder.hookSpecificOutput.additionalContext, /about 40 minutes/);
});

test("unknown sessions and unrelated events fail open", (t) => {
  const { env } = setup(t);
  assert.deepEqual(
    handleEvent({ hook_event_name: "PostToolUse", session_id: "missing" }, { now: 900_000, env }),
    {},
  );
  assert.deepEqual(
    handleEvent({ hook_event_name: "Stop", session_id: "s1" }, { now: 900_000, env }),
    {},
  );
});

test("shared config file overrides process environment", (t) => {
  const { env } = setup(t, 123_000);
  assert.equal(readInterval({ ...env, SMOKE_BREAK_INTERVAL_MS: "456000" }), 123_000);
});
