# Runtime Adapter (CLI-only)

## Goal
Use one stable execution path across Codex, Claude Code, and OpenClaw:
- bootstrap with `uv tool install psa-strategy-cli`,
- operate through `psa` commands only.

## Capability Selection
At runtime, detect capabilities in this order:
1. Can run `psa` directly?
2. If not, can run `uv tool install psa-strategy-cli`?
3. If still blocked, can user fix PATH (`uv tool update-shell`)?

Use the simplest available path that satisfies the task.

## CLI Path
- Preferred operational path: direct `psa ...`.
- Bootstrap path: `uv tool install psa-strategy-cli`.
- Do not use `uvx` in normal flow.
- If runtime remains unavailable, report blocker and stop.

## Memory Path
- Use CLI commands for read/upsert/evaluate flows.
- Use one logical save command for persistence (`upsert strategy-state`).
- Do not depend on local helper scripts.

## Presentation Path
- Start with readable comparison layout.
- If layout is unreadable, rerender as split table, ASCII block, or cards.
- Keep strategy meaning unchanged across render modes.

## User Communication
- Hide technical implementation details by default.
- Disclose details only when user asks, approval is required, or operation is blocked.
