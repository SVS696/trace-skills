#!/usr/bin/env node

import { createHash, randomUUID } from "node:crypto";
import {
  chmodSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  renameSync,
  statSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

export const DEFAULT_INTERVAL_MS = 5 * 60 * 1000;
const MAX_STATES = 1024;
const MAX_STATE_AGE_MS = 7 * 24 * 60 * 60 * 1000;

export function handleEvent(input, { now = Date.now(), env = process.env } = {}) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return {};
  const event = input.hook_event_name;
  const sessionId = input.session_id;
  if (typeof sessionId !== "string" || sessionId.length === 0) return {};
  if (event !== "UserPromptSubmit" && event !== "PostToolUse") return {};

  const stateDir = resolveStateDir(env);
  const statePath = join(stateDir, `${hashSession(sessionId)}.json`);

  if (event === "UserPromptSubmit") {
    const intervalMs = readInterval(env);
    ensureStateDir(stateDir);
    writeState(statePath, {
      startedAt: now,
      notifiedBucket: 0,
      intervalMs,
    });
    // State must exist even if best-effort cleanup is slow on a busy temporary directory.
    cleanupStates(stateDir, now);
    return {};
  }

  let state;
  try {
    state = JSON.parse(readFileSync(statePath, "utf8"));
  } catch {
    return {};
  }
  if (!validState(state)) return {};

  const elapsedMs = Math.max(0, now - state.startedAt);
  const bucket = Math.floor(elapsedMs / state.intervalMs);
  if (bucket === 0 || bucket <= state.notifiedBucket) return {};

  state.notifiedBucket = bucket;
  writeState(statePath, state);
  const elapsedMinutes = Math.max(1, Math.round(elapsedMs / 60_000));
  const minuteLabel = elapsedMinutes === 1 ? "minute" : "minutes";

  return {
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext:
        `Smoke break: this turn has been running for about ${elapsedMinutes} ${minuteLabel}. ` +
        "This is only a gentle checkpoint. Consider whether the work is progressing reasonably and " +
        "roughly according to plan. If so, or if any deviation seems modest, simply continue. " +
        "Only if it appears substantially off course or the time spent feels disproportionate, " +
        "consider whether changing approach or asking the user would help.",
    },
  };
}

export function readInterval(env = process.env) {
  const configPath = resolveConfigPath(env.SMOKE_BREAK_CONFIG_FILE);
  let fileValue;
  try {
    fileValue = parseEnv(readFileSync(configPath, "utf8")).SMOKE_BREAK_INTERVAL_MS;
  } catch {
    // Missing or unreadable optional config falls back to the process environment.
  }
  for (const raw of [fileValue, env.SMOKE_BREAK_INTERVAL_MS]) {
    if (raw === undefined) continue;
    const value = Number(raw);
    if (Number.isSafeInteger(value) && value > 0) return value;
  }
  return DEFAULT_INTERVAL_MS;
}

export function parseEnv(content) {
  const values = {};
  for (const rawLine of content.split(/\r?\n/u)) {
    const line = rawLine.trim();
    if (line === "" || line.startsWith("#")) continue;
    const match = /^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/u.exec(line);
    if (!match) continue;
    let value = match[2].trim();
    if (
      value.length >= 2 &&
      ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'")))
    ) {
      value = value.slice(1, -1);
    }
    values[match[1]] = value;
  }
  return values;
}

function resolveConfigPath(rawPath) {
  if (typeof rawPath !== "string" || rawPath.trim() === "") {
    return join(homedir(), ".smoke-break.env");
  }
  const value = rawPath.trim();
  if (value === "~") return homedir();
  if (value.startsWith("~/") || value.startsWith("~\\")) {
    return join(homedir(), value.slice(2));
  }
  return resolve(value);
}

function resolveStateDir(env) {
  if (typeof env.SMOKE_BREAK_STATE_DIR === "string" && env.SMOKE_BREAK_STATE_DIR.trim() !== "") {
    return resolve(env.SMOKE_BREAK_STATE_DIR.trim());
  }
  const uid = typeof process.getuid === "function" ? process.getuid() : "user";
  return join(tmpdir(), `claude-smoke-break-${uid}`);
}

function hashSession(sessionId) {
  return createHash("sha256").update(sessionId).digest("hex");
}

function ensureStateDir(stateDir) {
  mkdirSync(stateDir, { recursive: true, mode: 0o700 });
  try {
    chmodSync(stateDir, 0o700);
  } catch {
    // Best effort on filesystems without POSIX permissions.
  }
}

function writeState(path, state) {
  ensureStateDir(dirname(path));
  const temporary = `${path}.${process.pid}.${randomUUID()}.tmp`;
  try {
    writeFileSync(temporary, `${JSON.stringify(state)}\n`, { encoding: "utf8", mode: 0o600 });
    renameSync(temporary, path);
  } finally {
    try {
      unlinkSync(temporary);
    } catch {
      // renameSync removes the temporary path on success.
    }
  }
}

function validState(state) {
  return (
    state &&
    Number.isFinite(state.startedAt) &&
    Number.isSafeInteger(state.notifiedBucket) &&
    state.notifiedBucket >= 0 &&
    Number.isSafeInteger(state.intervalMs) &&
    state.intervalMs > 0
  );
}

function cleanupStates(stateDir, now) {
  let entries;
  try {
    entries = readdirSync(stateDir)
      .filter((name) => name.endsWith(".json"))
      .map((name) => {
        const path = join(stateDir, name);
        return { path, mtimeMs: statSync(path).mtimeMs };
      })
      .sort((a, b) => a.mtimeMs - b.mtimeMs);
  } catch {
    return;
  }
  const stale = entries.filter((entry) => now - entry.mtimeMs > MAX_STATE_AGE_MS);
  const overflow = entries.slice(0, Math.max(0, entries.length - MAX_STATES + 1));
  for (const entry of new Map([...stale, ...overflow].map((item) => [item.path, item])).values()) {
    try {
      unlinkSync(entry.path);
    } catch {
      // Cleanup is best effort and must not block the hook.
    }
  }
}

async function main() {
  try {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    process.stdout.write(`${JSON.stringify(handleEvent(input))}\n`);
  } catch (error) {
    process.stderr.write(`Smoke Break: ${error.message}\n`);
    process.stdout.write("{}\n");
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
