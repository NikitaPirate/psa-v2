# Architecture

## System role

`PSA Platform` is a monorepo workspace with two active runtime surfaces:

- pure computation core for directional share targets;
- AI-first CLI that stores strategies and append-only logs locally.

## Module map

Core:
- `core/src/psa_core/types.py` - immutable domain dataclasses.
- `core/src/psa_core/validation.py` - semantic validation.
- `core/src/psa_core/math.py` - pure math primitives.
- `core/src/psa_core/engine.py` - public evaluation API.
- `core/src/psa_core/contracts.py` - JSON-like payload adapters.

CLI:
- `cli/src/psa_cli/parser.py` - command model and arguments.
- `cli/src/psa_cli/app.py` - command lifecycle, JSON I/O, and error envelope.
- `cli/src/psa_cli/handlers.py` - command dispatch.
- `cli/src/psa_cli/store.py` - local strategy/log persistence.
- `cli/src/psa_cli/locks.py` - per-strategy write lock.
- `cli/src/psa_cli/schema.py` - request schema loading and validation.

## Local storage

Per working directory:

- `.psa/strategies/<strategy_id>/strategy.json`
- `.psa/strategies/<strategy_id>/log.ndjson`

Writes are synchronized by `.psa/strategies/<strategy_id>/.lock`.

## Data flow

1. Parse CLI arguments and enforce `--json`.
2. Validate input payload with command schema (for input-based commands).
3. For evaluate commands, load strategy by `strategy_id` from local storage.
4. Execute core evaluation or storage mutation.
5. Return stable JSON success payload or JSON error envelope.

## Validation split

- `core/contracts.py`: runtime adapter checks and conversion for core evaluation inputs.
- `core/validation.py`: semantic domain constraints and invariants.
- `cli/schema.py`: JSON Schema boundary checks for CLI payloads.
- `cli/store.py`: strategy/log existence and persistence integrity checks.

## Out of scope

- UI rendering.
- Order execution.
- Broker/exchange integrations.
- Regime auto-detection.
- Rebalancing strategy construction.
- Fee, commission, and slippage accounting.
- Network backends and remote storage.

## Cross-reference

- Domain objects: `docs/DOMAIN_MODEL.md`
- Math details: `docs/MATH_SPEC.md`
- Contracts: `docs/CONTRACTS.md`
