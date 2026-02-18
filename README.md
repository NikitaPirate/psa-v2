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
uv sync --group dev
```

## Run tests

```bash
uv run --group dev pytest
```

## Lint

```bash
uv run --group dev ruff check .
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

## Repository layout

- `src/psa_core/` - core package.
- `schemas/` - versioned JSON schemas.
- `examples/` - contract payload examples.
- `tests/` - unit, invariants, and contract tests.
- `docs/` - architecture and specs.
- `AGENTS.md` - contributor behavior and documentation rules.
