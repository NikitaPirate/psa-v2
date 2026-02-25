# Testing Strategy

## Test layers

1. Core unit tests (`core/tests/test_engine.py`, `core/tests/test_validation.py`)
- directional price behavior,
- time coefficient boundaries,
- deterministic row evaluation,
- overlap and mode validation.

2. Core property/invariant tests (`core/tests/test_invariants.py`)
- bounded shares,
- monotonic favorable-direction behavior,
- non-decreasing target share over time when `k(t)` is non-decreasing.

3. Core contract tests (`core/tests/test_contracts.py`)
- schema validity,
- examples validated against schemas,
- response payloads validated against response schemas,
- schema-level and runtime-level rejection checks.

4. CLI contract and storage tests (`cli/tests/`)
- parser-level command contract,
- schema loading/precedence,
- strategy upsert/list/show/exists workflows,
- append-only log workflows and tail ordering,
- evaluate-by-`strategy_id` workflows,
- JSON error envelope and exit-code behavior,
- lock contention timeout behavior.

5. Cross-surface consistency checks
- when the same strategy payload and observation input are used, evaluation outputs must match across entrypoints;
- strategy transfer as raw JSON text and as `.json` file content must preserve payload semantics.

## Execution

```bash
uv run pytest
```

## Quality gate

A phase is acceptable only when all test layers pass.
