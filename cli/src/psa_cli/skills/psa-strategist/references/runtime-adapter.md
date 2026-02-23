# Runtime Adapter (CLI-only)

## Goal
Use one stable execution path across Codex, Claude Code, and OpenClaw:
- operate through `psa` commands,
- allow only bootstrap exceptions required to make `psa` available.

## Source of Truth
All command permissions are defined in `references/command-authority.md`.

## Capability Selection
At runtime, detect capabilities in this order:
1. Can run `psa` directly?
2. If not, can run `uv tool install psa-strategy-cli`?
3. If still blocked, can user fix PATH (`uv tool update-shell`)?

Use the simplest path that satisfies `command-authority.md`.

## State Path
- Use CLI commands for read/upsert/evaluate/log flows.
- Strategy state in `strategy` entity.
- Cross-session rationale and check-ins in append-only `log` entity.

## Presentation Path
- Start with readable comparison layout.
- If layout is unreadable, rerender as split table, ASCII block, or cards.
- Keep strategy meaning unchanged across render modes.

## User Communication
- Hide technical implementation details by default.
- Disclose details only when user asks, approval is required, or operation is blocked.
