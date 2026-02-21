---
name: psa-strategist
description: Build and maintain investor-facing PSA strategies with persistent cross-session memory and non-proactive behavior using PSA CLI only (`psa` command via `psa-strategy-cli`).
---

# PSA Strategist

## Overview
Use this skill as a standalone PSA strategy agent. The operational interface is CLI-only: the agent works through `psa` commands and does not depend on local helper scripts.

## Operating Rules
- Keep non-proactive behavior. Act only on explicit user requests.
- Preserve user meaning, not only numeric parameters.
- Save only after explicit user confirmation.
- Use `psa` as the only task interface for read/upsert/evaluate actions.
- Keep versions in data model, but use latest version by default in normal flow.
- Use explicit `--version-id` only when user asks or when debugging historical behavior.
- Do not use `uvx` in normal workflow.
- Do not use `uv run python ...`, `memory_store.py`, or `render_strategy_view.py`.
- Do not instruct the user to prepare request/response files for normal flow.

## Runtime Policy
Package name is `psa-strategy-cli`, command is `psa`.

Resolution order:
1. Check runtime:
```bash
psa --version
```
2. If command is missing, install:
```bash
uv tool install psa-strategy-cli
psa --version
```
3. If still missing, report blocker and suggest:
```bash
uv tool update-shell
```

Blocking message meaning:
- "PSA CLI cannot run in this environment because `uv` or PATH configuration is missing. Install/configure `uv`, then I can continue."

## Quick Start
1. Ensure runtime with policy above.
2. Read current state:
```bash
psa show runtime
psa show memory --view summary
```
3. Execute requested flow from `references/workflow.md`.

## Workflow Selection
- First strategy creation or major redesign: `references/workflow.md` (First-Run Flow).
- PSA method boundaries: `references/domain-lock.md`.
- Conversation style: `references/dialog-playbook.md`.
- Memory payload fields: `references/memory-schema-v1.json`.
- Save postconditions: `references/memory-commit-policy.md`.
- Command patterns: `references/cli-recipes.md`.
- Runtime behavior in Codex/Claude/OpenClaw: `references/runtime-adapter.md`.
- Payload examples: `references/psa-json-templates.md`.
- User-facing output policy: `references/response-format.md`.

## CLI Command Map
Read:
- `psa show runtime`
- `psa show memory --view summary|full`
- `psa show strategy --id <strategy_id> --include versions --include theses --include checkins --include decisions`
- `psa show thesis --id <thesis_id>`

Upsert:
- `psa upsert thesis ...`
- `psa upsert strategy ... [--set-active]`
- `psa upsert profile ...`
- `psa upsert version ...`
- `psa upsert link --strategy-id ... --thesis-id ...`
- `psa upsert checkin ...`
- `psa upsert decision ...`
- `psa upsert strategy-state --json '<payload>'`

Evaluate:
- default latest-flow: `psa evaluate point|rows|ranges ...`
- optional override: `--version-id ...`
- optional latest by selected strategy: `--strategy-id ...`
- inline pre-save draft mode: `--market-mode ... --price-segment ... [--time-segment ...]`

## Persistence Contract
- Save only after explicit confirmation.
- Prefer one logical save command: `psa upsert strategy-state --json ...`.
- Keep stable IDs for thesis/strategy/version.
- Always keep rationale for versions and decisions.

## Presentation Policy
- Human summary first.
- Compact comparison (table/cards/ASCII) second.
- JSON only on explicit request or as technical appendix.
- Never force user to parse JSON to make a decision.
