from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import UTC, datetime

from psa_core.math import compute_price_share, compute_time_coefficient, compute_virtual_price
from psa_core.types import (
    EvaluationRow,
    ObservationRow,
    PortfolioEvaluation,
    PortfolioObservation,
    PriceSegment,
    StrategySpec,
)
from psa_core.validation import (
    validate_alignment_search_bounds,
    validate_observation,
    validate_portfolio_observation,
    validate_range_arguments,
    validate_strategy,
)


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


def _strategy_price_bounds(strategy: StrategySpec) -> tuple[float, float]:
    min_price = min(segment.price_low for segment in strategy.price_segments)
    max_price = max(segment.price_high for segment in strategy.price_segments)
    return float(min_price), float(max_price)


def _logspace(start: float, end: float, steps: int) -> list[float]:
    if steps < 2:
        raise ValueError("steps must be >= 2")
    if start <= 0 or end <= 0:
        raise ValueError("logspace bounds must be > 0")
    if start >= end:
        raise ValueError("logspace requires start < end")
    log_start = math.log(start)
    log_end = math.log(end)
    return [math.exp(value) for value in _linspace(log_start, log_end, steps)]


def _portfolio_share(usd_amount: float, asset_amount: float, price: float) -> float:
    denominator = usd_amount + asset_amount * price
    if denominator <= 0:
        return 0.0
    return float(asset_amount * price / denominator)


def _target_share_at_price(
    strategy: StrategySpec,
    *,
    price: float,
    time_k: float,
) -> float:
    virtual_price = compute_virtual_price(price, time_k, strategy.market_mode)
    return float(compute_price_share(virtual_price, strategy.price_segments, strategy.market_mode))


def _find_alignment_price(
    strategy: StrategySpec,
    *,
    time_k: float,
    current_price: float,
    usd_amount: float,
    asset_amount: float,
    min_price: float,
    max_price: float,
) -> float | None:
    grid = _logspace(min_price, max_price, 512)

    def f(price: float) -> float:
        current_share = _portfolio_share(usd_amount, asset_amount, price)
        target_share = _target_share_at_price(strategy, price=price, time_k=time_k)
        return current_share - target_share

    evaluated = [(price, f(price)) for price in grid]
    epsilon = 1e-12

    exact_roots = [price for price, value in evaluated if abs(value) <= epsilon]
    intervals: list[tuple[float, float]] = []
    for (left_price, left_value), (right_price, right_value) in zip(
        evaluated,
        evaluated[1:],
        strict=False,
    ):
        if left_value * right_value < 0:
            intervals.append((left_price, right_price))

    candidates = [(price, price) for price in exact_roots] + intervals
    if not candidates:
        return None

    bracket_low, bracket_high = min(
        candidates,
        key=lambda interval: abs((interval[0] + interval[1]) * 0.5 - current_price),
    )

    if abs(bracket_high - bracket_low) <= epsilon:
        return float(bracket_low)

    left = float(bracket_low)
    right = float(bracket_high)
    f_left = f(left)
    if abs(f_left) <= epsilon:
        return left
    if abs(f(right)) <= epsilon:
        return right

    for _ in range(60):
        mid = (left + right) * 0.5
        f_mid = f(mid)
        if abs(f_mid) <= epsilon:
            return float(mid)
        if f_left * f_mid <= 0:
            right = mid
        else:
            left = mid
            f_left = f_mid

    return float((left + right) * 0.5)


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


def evaluate_portfolio(
    strategy: StrategySpec,
    observation: PortfolioObservation,
) -> PortfolioEvaluation:
    validate_strategy(strategy)
    validate_portfolio_observation(
        timestamp=observation.timestamp,
        price=observation.price,
        usd_amount=observation.usd_amount,
        asset_amount=observation.asset_amount,
        avg_entry_price=observation.avg_entry_price,
    )
    validate_alignment_search_bounds(
        min_price=observation.alignment_search_min_price,
        max_price=observation.alignment_search_max_price,
    )

    time_k = compute_time_coefficient(observation.timestamp, strategy.time_segments)
    virtual_price = compute_virtual_price(observation.price, time_k, strategy.market_mode)
    target_share = compute_price_share(virtual_price, strategy.price_segments, strategy.market_mode)

    portfolio_value_usd = observation.usd_amount + observation.asset_amount * observation.price
    asset_value_usd = observation.asset_amount * observation.price
    usd_value_usd = observation.usd_amount
    base_share = _portfolio_share(
        observation.usd_amount, observation.asset_amount, observation.price
    )
    share_deviation = base_share - target_share

    target_asset_value_usd = target_share * portfolio_value_usd
    target_asset_amount = target_asset_value_usd / observation.price
    asset_amount_delta = target_asset_amount - observation.asset_amount
    usd_delta = -asset_amount_delta * observation.price

    strategy_min_price, strategy_max_price = _strategy_price_bounds(strategy)
    min_search_price = (
        observation.alignment_search_min_price
        if observation.alignment_search_min_price is not None
        else strategy_min_price * 0.2
    )
    max_search_price = (
        observation.alignment_search_max_price
        if observation.alignment_search_max_price is not None
        else strategy_max_price * 5.0
    )
    validate_alignment_search_bounds(min_price=min_search_price, max_price=max_search_price)

    alignment_price = _find_alignment_price(
        strategy,
        time_k=float(time_k),
        current_price=observation.price,
        usd_amount=observation.usd_amount,
        asset_amount=observation.asset_amount,
        min_price=float(min_search_price),
        max_price=float(max_search_price),
    )

    avg_entry_pnl_usd: float | None = None
    avg_entry_pnl_pct: float | None = None
    if observation.avg_entry_price is not None:
        avg_entry_pnl_usd = observation.asset_amount * (
            observation.price - observation.avg_entry_price
        )
        avg_entry_pnl_pct = (observation.price / observation.avg_entry_price) - 1.0

    return PortfolioEvaluation(
        timestamp=observation.timestamp,
        price=float(observation.price),
        time_k=float(time_k),
        virtual_price=float(virtual_price),
        base_share=float(base_share),
        target_share=float(target_share),
        share_deviation=float(share_deviation),
        portfolio_value_usd=float(portfolio_value_usd),
        asset_value_usd=float(asset_value_usd),
        usd_value_usd=float(usd_value_usd),
        target_asset_value_usd=float(target_asset_value_usd),
        target_asset_amount=float(target_asset_amount),
        asset_amount_delta=float(asset_amount_delta),
        usd_delta=float(usd_delta),
        alignment_price=float(alignment_price) if alignment_price is not None else None,
        avg_entry_price=float(observation.avg_entry_price)
        if observation.avg_entry_price is not None
        else None,
        avg_entry_pnl_usd=float(avg_entry_pnl_usd) if avg_entry_pnl_usd is not None else None,
        avg_entry_pnl_pct=float(avg_entry_pnl_pct) if avg_entry_pnl_pct is not None else None,
    )
