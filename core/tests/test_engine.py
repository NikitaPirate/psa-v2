from __future__ import annotations

import pytest
from psa_core import (
    ObservationRow,
    PriceSegment,
    StrategySpec,
    TimeSegment,
    build_rows_from_ranges,
    evaluate_point,
    evaluate_rows,
    evaluate_rows_from_ranges,
)
from psa_core.math import compute_time_coefficient


def _bear_strategy() -> StrategySpec:
    return StrategySpec(
        market_mode="bear",
        price_segments=(
            PriceSegment(price_low=50_000, price_high=60_000, weight=10),
            PriceSegment(price_low=40_000, price_high=50_000, weight=30),
            PriceSegment(price_low=30_000, price_high=40_000, weight=40),
            PriceSegment(price_low=25_000, price_high=30_000, weight=20),
        ),
        time_segments=(
            TimeSegment(
                start_ts="2026-01-01T00:00:00Z",
                end_ts="2026-06-01T00:00:00Z",
                k_start=1.0,
                k_end=1.8,
            ),
        ),
    )


def _bull_strategy() -> StrategySpec:
    return StrategySpec(
        market_mode="bull",
        price_segments=(
            PriceSegment(price_low=25_000, price_high=35_000, weight=20),
            PriceSegment(price_low=35_000, price_high=50_000, weight=30),
            PriceSegment(price_low=50_000, price_high=70_000, weight=50),
        ),
        time_segments=(
            TimeSegment(
                start_ts="2026-01-01T00:00:00Z",
                end_ts="2026-12-31T00:00:00Z",
                k_start=1.0,
                k_end=1.4,
            ),
        ),
    )


def test_piecewise_share_is_directional_by_market_mode() -> None:
    bear = _bear_strategy()
    bull = _bull_strategy()

    bear_high = evaluate_point(bear, "2026-03-01T00:00:00Z", 58_000)
    bear_low = evaluate_point(bear, "2026-03-01T00:00:00Z", 32_000)
    assert bear_low.base_share > bear_high.base_share

    bull_low = evaluate_point(bull, "2026-09-01T00:00:00Z", 32_000)
    bull_high = evaluate_point(bull, "2026-09-01T00:00:00Z", 65_000)
    assert bull_high.base_share > bull_low.base_share


def test_time_coefficient_boundaries_and_midpoint() -> None:
    time_segments = (
        TimeSegment(
            start_ts="2026-01-01T00:00:00Z",
            end_ts="2026-01-11T00:00:00Z",
            k_start=1.0,
            k_end=2.0,
        ),
    )

    assert compute_time_coefficient("2025-12-31T00:00:00Z", time_segments) == 1.0
    assert abs(compute_time_coefficient("2026-01-06T00:00:00Z", time_segments) - 1.5) < 1e-9
    assert compute_time_coefficient("2026-01-20T00:00:00Z", time_segments) == 2.0


def test_market_mode_changes_virtual_price_direction() -> None:
    bear = _bear_strategy()
    bull = _bull_strategy()

    bear_row = evaluate_point(bear, "2026-03-01T00:00:00Z", 42_000)
    bull_row = evaluate_point(bull, "2026-09-01T00:00:00Z", 56_000)

    assert bear_row.virtual_price < bear_row.price
    assert bull_row.virtual_price > bull_row.price
    assert bear_row.target_share >= bear_row.base_share
    assert bull_row.target_share >= bull_row.base_share


def test_evaluate_rows_is_deterministic_and_preserves_order() -> None:
    strategy = _bear_strategy()
    rows = [
        ObservationRow(timestamp="2026-02-01T00:00:00Z", price=47_000),
        ObservationRow(timestamp="2026-03-01T00:00:00Z", price=44_000),
        ObservationRow(timestamp="2026-04-01T00:00:00Z", price=41_000),
    ]

    first = evaluate_rows(strategy, rows)
    second = evaluate_rows(strategy, rows)

    assert first == second
    assert [row.timestamp for row in first] == [row.timestamp for row in rows]


def test_build_rows_from_ranges_includes_price_breakpoints() -> None:
    strategy = _bear_strategy()
    rows = build_rows_from_ranges(
        strategy,
        price_start=60_000,
        price_end=25_000,
        price_steps=4,
        time_start="2026-02-01T00:00:00Z",
        time_end="2026-04-01T00:00:00Z",
        time_steps=3,
        include_price_breakpoints=True,
    )

    prices_first_ts = [row.price for row in rows if row.timestamp == rows[0].timestamp]
    assert 50_000 in prices_first_ts
    assert 40_000 in prices_first_ts
    assert 30_000 in prices_first_ts
    assert prices_first_ts == sorted(prices_first_ts, reverse=True)
    assert len(rows) == 3 * len(prices_first_ts)


def test_evaluate_rows_from_ranges_calls_evaluate_rows_flow() -> None:
    strategy = _bear_strategy()
    evaluated = evaluate_rows_from_ranges(
        strategy,
        price_start=60_000,
        price_end=25_000,
        price_steps=4,
        time_start="2026-02-01T00:00:00Z",
        time_end="2026-04-01T00:00:00Z",
        time_steps=3,
        include_price_breakpoints=True,
    )

    assert len(evaluated) > 0
    assert all(0 <= row.base_share <= 1 for row in evaluated)
    assert all(0 <= row.target_share <= 1 for row in evaluated)


def test_build_rows_from_ranges_rejects_non_integer_steps() -> None:
    strategy = _bear_strategy()

    with pytest.raises(ValueError, match="price_steps must be an integer >= 1"):
        build_rows_from_ranges(
            strategy,
            price_start=60_000,
            price_end=25_000,
            price_steps=2.9,  # type: ignore[arg-type]
            time_start="2026-02-01T00:00:00Z",
            time_end="2026-04-01T00:00:00Z",
            time_steps=3,
        )

    with pytest.raises(ValueError, match="time_steps must be an integer >= 1"):
        build_rows_from_ranges(
            strategy,
            price_start=60_000,
            price_end=25_000,
            price_steps=3,
            time_start="2026-02-01T00:00:00Z",
            time_end="2026-04-01T00:00:00Z",
            time_steps=1.9,  # type: ignore[arg-type]
        )


def test_build_rows_from_ranges_rejects_bool_steps() -> None:
    strategy = _bear_strategy()

    with pytest.raises(ValueError, match="price_steps must be an integer >= 1"):
        build_rows_from_ranges(
            strategy,
            price_start=60_000,
            price_end=25_000,
            price_steps=True,  # type: ignore[arg-type]
            time_start="2026-02-01T00:00:00Z",
            time_end="2026-04-01T00:00:00Z",
            time_steps=3,
        )

    with pytest.raises(ValueError, match="time_steps must be an integer >= 1"):
        build_rows_from_ranges(
            strategy,
            price_start=60_000,
            price_end=25_000,
            price_steps=3,
            time_start="2026-02-01T00:00:00Z",
            time_end="2026-04-01T00:00:00Z",
            time_steps=False,  # type: ignore[arg-type]
        )
