# Memory Commit Policy

## Purpose
Define required postconditions after `save`, independent of runtime environment.

## Save Trigger
- Persist only after explicit user confirmation (`save`, `сохраняй`, `фиксируй`).
- Do not write strategy/thesis updates in background mode.

## Required Postconditions
After successful strategy save, memory must contain:
1. Thesis record with stable `id`.
2. Strategy record with stable `id`.
3. Strategy version record with `strategy_spec` and `rationale`.
4. Link between strategy and thesis.
5. `user_profile.active_strategy_id` aligned with saved strategy when requested.

## Logical Commit Rule
- Use one logical commit boundary per user save action.
- Prefer: `psa upsert strategy-state --json ...`.

## Write-Method Contract
- The skill must persist via PSA CLI operations.
- Do not depend on local helper scripts for memory writes.
- Keep save behavior deterministic and atomic from user perspective.

## Failure Handling
- If persistence fails, report failure clearly and do not claim saved state.
- If partial writes are detected, report what succeeded and what remains unsaved.
