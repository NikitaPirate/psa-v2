# PSA Platform

Monorepo workspace for PSA tooling (engine, CLI, API, integrations).  
Current implemented modules: deterministic computation core plus AI-first stateful CLI for strategy/log workflows.

## Scope (Phase 0)

- Monorepo foundation with implemented core module (no UI, no broker/exchange integration yet).
- Single mode axis: `market_mode`.
  - `bear` means accumulation behavior.
  - `bull` means distribution behavior.
- Strict input/output contracts via versioned JSON Schema.
- Share outputs are normalized to `[0, 1]`.

## Design Principles

- Keep core logic framework-free.
- Keep behavior deterministic: same input -> same output.
- Keep validation explicit at boundaries.
- Keep the model abstract: no rebalancing logic, no fee/commission/slippage accounting.

## Installation

Works in `bash`, `zsh`, and `fish`.

```bash
uv sync
```

## CLI for users

The published CLI package name is `psa-strategy-cli`, while the executable command is `psa`.

Run without installing:

```bash
uvx --from psa-strategy-cli psa --version
```

Install globally as a tool:

```bash
uv tool install psa-strategy-cli
psa --version
```

Stateful CLI storage layout (inside current working directory):

- `.psa/strategies/<strategy_id>/strategy.json`
- `.psa/strategies/<strategy_id>/log.ndjson`

Core command groups:

- `psa strategy ...` for strategy CRUD-lite (`upsert/list/show/exists`)
- `psa log ...` for append-only journal (`append/list/show/tail`)
- `psa evaluate-* --strategy-id <id>` for computation over persisted strategies

## Run tests

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Public Python API

- `evaluate_point(strategy, timestamp, price) -> EvaluationRow`
- `evaluate_rows(strategy, rows) -> list[EvaluationRow]`
- `build_rows_from_ranges(...) -> list[ObservationRow]`
- `evaluate_rows_from_ranges(...) -> list[EvaluationRow]`

See:
- domain objects: `docs/DOMAIN_MODEL.md`
- formulas and invariants: `docs/MATH_SPEC.md`
- JSON contracts and examples: `docs/CONTRACTS.md`
- test matrix: `docs/TESTING_STRATEGY.md`
- release process: `docs/RELEASE_RUNBOOK.md`

## Repository layout

- `core/src/psa_core/` - core package.
- `cli/src/psa_cli/` - CLI package.
- `api/src/psa_api/` - FastAPI package.
- `schemas/` - versioned JSON schemas.
- `examples/` - contract payload examples.
- `core/tests/` - core unit, invariants, and contract tests.
- `docs/` - architecture and specs.
- `AGENTS.md` - contributor behavior and documentation rules.
