# PSA Platform

Monorepo workspace for PSA tooling (engine, CLI, API, integrations).  
Current implemented module: a compact, deterministic Python core for directional `price × time` share strategies designed for LLM agents.

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
