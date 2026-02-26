# Testing Strategy

## Test layers

1. Core unit tests (`core/tests/test_engine.py`, `core/tests/test_validation.py`)
- directional price behavior,
- time coefficient boundaries,
- deterministic row evaluation,
- overlap and mode validation,
- portfolio evaluation fields and alignment-price search behavior.

2. Core property/invariant tests (`core/tests/test_invariants.py`)
- bounded shares,
- monotonic favorable-direction behavior,
- non-decreasing target share over time when `k(t)` is non-decreasing.

3. Core contract tests (`core/tests/test_contracts.py`)
- schema validity,
- examples validated against schemas,
- response payloads validated against response schemas,
- schema-level and runtime-level rejection checks,
- `evaluate_portfolio` request/response payload validation.

4. CLI contract and storage tests (`cli/tests/`)
- parser-level command contract,
- schema loading/precedence,
- strategy upsert/list/show/exists workflows,
- append-only log workflows and tail ordering,
- evaluate-by-`strategy_id` workflows,
- `evaluate-portfolio` workflow,
- JSON error envelope and exit-code behavior,
- lock contention timeout behavior.

5. Cross-surface consistency checks
- when the same strategy payload and observation input are used, evaluation outputs must match across entrypoints;
- strategy transfer as raw JSON text and as `.json` file content must preserve payload semantics.

6. API contract tests (`api/tests/`)
- `POST /v1/evaluate/portfolio` positive/negative paths,
- OpenAPI path exposure for portfolio evaluation.

7. Web quality checks (`web/`)
- TypeScript static check (`npm run typecheck`);
- Unit/UI tests in run mode (`npm run test:ci`);
- Production build check (`npm run build`).

## Execution

```bash
uv run pytest
npm --prefix web run typecheck
npm --prefix web run test:ci
npm --prefix web run build
```

## Quality gate

A phase is acceptable only when all listed test layers and static checks pass.
