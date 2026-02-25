# PSA Platform

Monorepo workspace for PSA tooling (engine, CLI, API, integrations).  
Current implemented modules: deterministic computation core plus AI-first stateful CLI for strategy/log workflows.

## Scope (Phase 0)

- Monorepo foundation with implemented core, API, CLI, and local web client.
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

## Getting Started (AI agent)

The published CLI package name is `psa-strategy-cli`, while the executable command is `psa`.

1. Install CLI:

```bash
uv tool install psa-strategy-cli
psa --version
```

2. Install `psa-strategist` skill for your runtime:

```bash
psa install-skill codex --json
```

Other common runtimes:

```bash
psa install-skill claude --json
psa install-skill opencode --json
psa install-skill openclaw --json
```

Custom installation directories:

```bash
psa install-skill openclaw --skills-dir /path/to/skills-dir --json
psa install-skill codex --skills-dir /path/to/skills-dir --agents-dir /path/to/agents-dir --json
```

Unknown runtime:

```bash
psa install-skill any-runtime --skills-dir /path/to/skills-dir --json
```

Full runtime list:

```bash
psa install-skill --help
```

3. Start your AI agent and activate the skill.

Codex:

```text
Use $psa-strategist and explain PSA in plain language.
```

Claude Code:

```text
/psa-strategist Explain PSA in plain language.
```

Example follow-up (any runtime after skill activation):

```text
I think asset A may drop to point m. I want to start buying slowly from point n. Then from x to y, I want to buy faster, up to about 2x the pace.
```

Stateful CLI storage layout (inside current working directory):

- `.psa/strategies/<strategy_id>/strategy.json`
- `.psa/strategies/<strategy_id>/log.ndjson`

## CLI reference (short)

- `psa strategy ...` - strategy CRUD-lite (`upsert/list/show/exists`)
- `psa log ...` - append-only journal (`append/list/show/tail`)
- `psa evaluate-* --strategy-id <id>` - deterministic evaluation using stored strategies
- `psa install-skill <runtime> [--skills-dir /path/to/skills-dir] [--agents-dir /path/to/agents-dir] --json` - install `psa-strategist` for target runtime

## Web: Create / Use

Local web client for canonical strategy editing and evaluation via API/core.

What it does:
- `Create` mode:
  - canonical strategy JSON editor + explicit `Apply JSON`;
  - form controls for `market_mode`, `price_segments`, `time_segments`;
  - weight allocation helper (rebalance + lock).
- `Use` mode:
  - evaluate `now` and custom point (`timestamp`, `price`);
  - line chart: `Price vs Share (without time modifier)`;
  - heatmap + 3D only when `time_segments` are present.
- Docs mode:
  - isolated docs page at `/docs/en` and `/docs/ru` (main app UI remains English).
- API-first chart/evaluation flow:
  - `POST /v1/evaluate/point`
  - `POST /v1/evaluate/rows`
  - `POST /v1/evaluate/rows-from-ranges`

Start API:

```bash
uv run uvicorn psa_api.main:app --reload
```

Start web app:

```bash
cd web
npm install
npm run dev
```

## Web notes

- Web client does not re-implement model math in frontend.
- Complex analytics beyond current core/API contracts stay out of scope for web layer.

## Run tests

```bash
uv run pytest
npm --prefix web run test:ci
```

## Static checks

```bash
uv run ruff check .
uv run pyright
npm --prefix web run typecheck
npm --prefix web run build
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
- `web/` - React + Vite local client (`Create / Use`, API-first evaluation).
- `skills/` - agent skill definitions and reference playbooks.
- `schemas/` - versioned JSON schemas.
- `examples/` - contract payload examples.
- `core/tests/` - core unit, invariants, and contract tests.
- `docs/` - architecture and specs.
- `AGENTS.md` - contributor behavior and documentation rules.
