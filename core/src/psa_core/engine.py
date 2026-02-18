from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from psa_core.math import compute_price_share, compute_time_coefficient, compute_virtual_price
from psa_core.types import EvaluationRow, ObservationRow, PriceSegment, StrategySpec
from psa_core.validation import validate_observation, validate_range_arguments, validate_strategy


def _linspace(start: float, end: float, steps: int) -> list[float]:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if steps == 1:
        return [float(start)]
    step_size = (end - start) / float(steps - 1)
    return [float(start + step_size * idx) for idx in range(steps)]


def _unique_sorted(values: Sequence[float], *, reverse: bool) -> list[float]:
    ordered = sorted(float(value) for value in values)
    deduped: list[float] = []
    for value in ordered:
        if not deduped or abs(value - deduped[-1]) > 1e-9:
            deduped.append(value)
    if reverse:
        deduped.reverse()
    return deduped


def _price_breakpoints_in_range(
    segments: Sequence[PriceSegment],
    range_low: float,
    range_high: float,
) -> list[float]:
    points: list[float] = []
    for segment in segments:
        if range_low <= segment.price_low <= range_high:
            points.append(float(segment.price_low))
        if range_low <= segment.price_high <= range_high:
            points.append(float(segment.price_high))
    return points


def _to_iso_z(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat().replace("+00:00", "Z")


def evaluate_point(strategy: StrategySpec, timestamp: str, price: float) -> EvaluationRow:
    validate_strategy(strategy)
    validate_observation(timestamp, price)

    time_k = compute_time_coefficient(timestamp, strategy.time_segments)
    base_share = compute_price_share(price, strategy.price_segments, strategy.market_mode)
    virtual_price = compute_virtual_price(price, time_k, strategy.market_mode)
    target_share = compute_price_share(
        virtual_price,
        strategy.price_segments,
        strategy.market_mode,
    )

    return EvaluationRow(
        timestamp=timestamp,
        price=float(price),
        time_k=float(time_k),
        virtual_price=float(virtual_price),
        base_share=float(base_share),
        target_share=float(target_share),
    )


def evaluate_rows(strategy: StrategySpec, rows: Sequence[ObservationRow]) -> list[EvaluationRow]:
    validate_strategy(strategy)
    output: list[EvaluationRow] = []
    for row in rows:
        output.append(evaluate_point(strategy=strategy, timestamp=row.timestamp, price=row.price))
    return output


def build_rows_from_ranges(
    strategy: StrategySpec,
    *,
    price_start: float,
    price_end: float,
    price_steps: int,
    time_start: str,
    time_end: str,
    time_steps: int,
    include_price_breakpoints: bool = True,
) -> list[ObservationRow]:
    validate_strategy(strategy)
    start_ts, end_ts = validate_range_arguments(
        price_start=price_start,
        price_end=price_end,
        price_steps=price_steps,
        time_start=time_start,
        time_end=time_end,
        time_steps=time_steps,
    )

    price_points = _linspace(float(price_start), float(price_end), price_steps)
    if include_price_breakpoints:
        low = min(float(price_start), float(price_end))
        high = max(float(price_start), float(price_end))
        price_points.extend(_price_breakpoints_in_range(strategy.price_segments, low, high))

    descending_price = float(price_end) < float(price_start)
    unique_prices = _unique_sorted(price_points, reverse=descending_price)

    start_s = start_ts.timestamp()
    end_s = end_ts.timestamp()
    time_points = _linspace(start_s, end_s, time_steps)
    time_datetimes = [datetime.fromtimestamp(point, tz=UTC) for point in time_points]
    time_iso = [_to_iso_z(ts) for ts in time_datetimes]

    rows: list[ObservationRow] = []
    for ts in time_iso:
        for price in unique_prices:
            rows.append(ObservationRow(timestamp=ts, price=price))
    return rows


def evaluate_rows_from_ranges(
    strategy: StrategySpec,
    *,
    price_start: float,
    price_end: float,
    price_steps: int,
    time_start: str,
    time_end: str,
    time_steps: int,
    include_price_breakpoints: bool = True,
) -> list[EvaluationRow]:
    rows = build_rows_from_ranges(
        strategy,
        price_start=price_start,
        price_end=price_end,
        price_steps=price_steps,
        time_start=time_start,
        time_end=time_end,
        time_steps=time_steps,
        include_price_breakpoints=include_price_breakpoints,
    )
    return evaluate_rows(strategy=strategy, rows=rows)
