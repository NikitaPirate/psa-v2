# Testing Strategy

## Test layers

1. Unit tests (`tests/test_engine.py`, `tests/test_validation.py`)
- directional price behavior,
- time coefficient boundaries,
- deterministic row evaluation,
- overlap and mode validation.

2. Property/invariant tests (`tests/test_invariants.py`)
- bounded shares,
- monotonic favorable-direction behavior,
- non-decreasing target share over time when `k(t)` is non-decreasing.

3. Contract tests (`tests/test_contracts.py`)
- schema validity,
- examples validated against schemas,
- response payloads validated against response schemas,
- schema-level and runtime-level rejection checks.

## Execution

```bash
uv run --group dev pytest
```

## Quality gate

A phase is acceptable only when all layers pass.
