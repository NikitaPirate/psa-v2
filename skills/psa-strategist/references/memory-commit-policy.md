# Memory Commit Policy

## Purpose
Define what must be true in memory after `save`, independent of how the agent writes files.

## Save Trigger
- Persist only after explicit user confirmation such as "save", "сохраняй", "фиксируй".
- Do not write strategy/thesis updates in background mode.

## Required Postconditions
After a successful strategy save, memory must contain:
1. Thesis record with stable `id`.
2. Strategy record with stable `id`.
3. Strategy version record with `strategy_spec` and `rationale`.
4. Link between strategy and thesis.
5. `user_profile.active_strategy_id` aligned with the saved strategy (if user requested active).

## Logical Commit Rule
- Prefer one logical commit boundary per user save action.
- If using `memory_store.py`, use `batch` with `ops` (or `operations`) to reduce partial writes.
- If using native write/edit APIs, write one consistent final state snapshot.

## Write-Method Independence
Allowed write paths include:
- CLI-based apply (`memory_store.py`),
- direct file write/edit tools,
- other environment-native safe file operations.

The method is implementation detail. The postconditions above are normative.

## Failure Handling
- If persistence fails, report failure clearly and do not claim saved state.
- If partial writes happened, report what succeeded and what remains unsaved.
