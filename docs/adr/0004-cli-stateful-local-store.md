# ADR 0004: Stateful Local Store for AI-first CLI

## Status
Accepted

## Context
The CLI originally evaluated strategies from inline request payloads only.
Agent workflows require persistent strategy and journal state without direct file editing.

## Decision
- Introduce local per-workdir storage:
  - `.psa/strategies/<strategy_id>/strategy.json`
  - `.psa/strategies/<strategy_id>/log.ndjson`
- Keep strategy mutation as `upsert` and log mutation as append-only.
- Use per-strategy file lock (`.lock`) for write operations.
- Keep `evaluate-*` commands, but load strategy by `--strategy-id`.
- Require `--json` on operational commands and return unified JSON error payloads.

## Consequences
- Agent-friendly non-interactive contract with deterministic machine-readable output.
- Multi-strategy workflows without direct filesystem manipulation by the agent.
- Additional CLI complexity around persistence, locking, and storage integrity checks.
