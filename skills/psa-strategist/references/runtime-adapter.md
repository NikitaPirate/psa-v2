# Runtime Adapter

## Goal
Choose the least-friction execution path for the current agent environment without overloading the user with technical details.

## Capability-First Selection
At runtime, detect capabilities in this order:
1. Can run CLI commands (`uvx` or `uv`)?
2. Can write local files directly?
3. Is permission escalation required for selected path?

Use the simplest available path that satisfies requested task.

## CLI Path
- Prefer `uvx --from psa-strategy-cli psa ...`.
- Fallback to `uv tool install psa-strategy-cli` only when `uvx` is unavailable.
- If neither is available, report blocker and stop execution path cleanly.

## Memory Path
- Follow `memory-commit-policy.md` postconditions.
- Prefer one logical commit operation.
- Do not force one command style (`cat <<'JSON'`, `Write`, etc.) as mandatory across environments.

## Presentation Path
- Start with readable comparison layout.
- If client breaks table rendering, switch to split table, ASCII block, or cards.
- Keep strategy meaning unchanged when switching layout.

## User Communication
- Hide implementation details by default.
- Disclose technical method only when:
  - user asks,
  - permission approval is needed,
  - operation is blocked.
