# Architecture

## System role

`PSA Platform` is a monorepo workspace with one computation core and multiple interaction surfaces.

The core stays the only source of computation semantics.
Other modules expose the same semantics through different runtime surfaces (CLI, API, UI clients, agent clients).

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

API:
- `api/src/psa_api/main.py` - FastAPI app assembly.
- `api/src/psa_api/routes.py` - HTTP route handlers.
- `api/src/psa_api/schema_validation.py` - request/response schema checks.
- `api/src/psa_api/errors.py` - JSON error envelope mapping.

Web:
- `web/src/App.tsx` - `Create / Use` interaction entrypoint.
- `web/src/main.tsx` - React bootstrap.
- `web/src/styles.css` - local UI styling.

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
- `api/src/psa_api/schema_validation.py`: JSON Schema boundary checks for HTTP payloads.
- `cli/store.py`: strategy/log existence and persistence integrity checks.

## Scenario model

One toolset supports two scenario families:

- strategy creation and adjustment;
- strategy usage and evaluation.

These scenarios are intentionally separated at UX-flow level, but they are not separate products.
A user can move between both flows without changing the underlying toolset or contracts.

## Cross-surface integration

- Agent, CLI, and web flows exchange strategy data via canonical JSON payloads.
- Data portability is a first-class requirement: the same strategy payload must remain valid across surfaces.
- Transfer format stays plain JSON text or `.json` file content; no mandatory bridge format is introduced.

## Out of scope

- Order execution.
- Broker/exchange integrations.
- Regime auto-detection.
- Rebalancing strategy construction.
- Fee, commission, and slippage accounting.
- Hosted multi-tenant storage backends.

## Cross-reference

- Domain objects: `docs/DOMAIN_MODEL.md`
- Math details: `docs/MATH_SPEC.md`
- Contracts: `docs/CONTRACTS.md`
