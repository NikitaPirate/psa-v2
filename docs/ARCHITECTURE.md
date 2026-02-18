# Architecture

## System role

`PSA Platform` is a monorepo workspace. In phase 0, implemented functionality is a pure computation core for directional share targets.

Inputs:
- strategy definition,
- timestamp,
- market price.

Outputs:
- numeric evaluation row(s) for machine consumption.

## Module map

- `psa_core/types.py` - immutable domain dataclasses.
- `psa_core/validation.py` - semantic validation for domain and API-level parameters.
- `psa_core/math.py` - pure math primitives.
- `psa_core/engine.py` - public evaluation API.
- `psa_core/contracts.py` - JSON-like payload adapters.

## Validation split

- `contracts.py`: validates raw payload shape/types for external JSON-like input.
- `validation.py`: validates semantic constraints used by the core (strategy invariants, point/range arguments).
- `engine.py`: orchestration and computation only; it calls validators instead of owning semantic rules.

## Data flow

1. Parse and validate boundary payloads.
2. Evaluate time coefficient `k(t)`.
3. Evaluate base share on real price.
4. Compute virtual price from `market_mode` and `k(t)`.
5. Evaluate target share.
6. Return stable, order-preserving rows.

## Out of scope

- UI rendering.
- Order execution.
- Broker/exchange integrations.
- Regime auto-detection.
- Rebalancing strategy construction.
- Fee, commission, and slippage accounting.
- Portfolio optimization; this package provides abstract conditional math models only.

## Cross-reference

- Domain objects: `docs/DOMAIN_MODEL.md`
- Math details: `docs/MATH_SPEC.md`
- Contracts: `docs/CONTRACTS.md`
