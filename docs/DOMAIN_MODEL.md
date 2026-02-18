# Domain Model

All public domain objects are immutable dataclasses (`frozen=True`, `slots=True`).

## Types

### `PriceSegment`
- `price_low: float`
- `price_high: float`
- `weight: float`

Weight rules:
- each weight must be `>= 0`;
- at least one segment must have `weight > 0` (total weight must be positive).

### `TimeSegment`
- `start_ts: str` (ISO-8601 with timezone)
- `end_ts: str` (ISO-8601 with timezone)
- `k_start: float`
- `k_end: float`

### `StrategySpec`
- `market_mode: "bear" | "bull"`
- `price_segments: tuple[PriceSegment, ...]`
- `time_segments: tuple[TimeSegment, ...]`

### `ObservationRow`
- `timestamp: str`
- `price: float`

### `EvaluationRow`
- `timestamp: str`
- `price: float`
- `time_k: float`
- `virtual_price: float`
- `base_share: float`
- `target_share: float`

Both share fields are normalized to `[0, 1]`.

## Public API

- `evaluate_point(strategy, timestamp, price) -> EvaluationRow`
- `evaluate_rows(strategy, rows) -> list[EvaluationRow]`
- `build_rows_from_ranges(...) -> list[ObservationRow]`
- `evaluate_rows_from_ranges(...) -> list[EvaluationRow]`

## Semantics lock

`market_mode` is the only direction field:
- `bear` => accumulation semantics.
- `bull` => distribution semantics.

No additional side/regime fields are allowed.
