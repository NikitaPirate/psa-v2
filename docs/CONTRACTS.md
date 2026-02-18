# Contracts

Machine-facing contracts are versioned JSON Schema files under `schemas/`.

## Request schemas

- `schemas/evaluate_point.request.v1.json`
- `schemas/evaluate_rows.request.v1.json`
- `schemas/evaluate_rows_from_ranges.request.v1.json`

## Response schemas

- `schemas/evaluate_point.response.v1.json`
- `schemas/evaluate_rows.response.v1.json`

## Contract notes

- Time fields use ISO-8601 date-time strings with timezone.
- `market_mode` enum is fixed to `bear | bull`.
- Output shares are normalized to `[0, 1]`.
- `price_segments` must include at least one row with `weight > 0`.
- Schema checks structure and primitive constraints.
- Cross-field and semantic constraints are enforced in `core/src/psa_core/validation.py`.

## Examples

- `examples/bear_accumulate_point.json`
- `examples/bull_distribute_point.json`
- `examples/batch_timeseries_rows.json`
- `examples/range_timeseries_rows.json`

## Runtime adapters

`core/src/psa_core/contracts.py` exposes payload adapters:
- request parsing,
- runtime validation delegation,
- JSON-ready response building.
- `evaluate_rows_from_ranges_payload` builds rows from range inputs and then delegates evaluation.
