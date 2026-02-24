from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st
from psa_core import PriceSegment, StrategySpec, TimeSegment, evaluate_point

BASE_TS = datetime(2026, 1, 1, tzinfo=UTC)


def _iso(day_offset: int) -> str:
    return (BASE_TS + timedelta(days=day_offset)).isoformat().replace("+00:00", "Z")


def _strategy(market_mode: str) -> StrategySpec:
    return StrategySpec(
        market_mode=market_mode,  # type: ignore[arg-type]
        price_segments=(
            PriceSegment(price_low=50_000, price_high=60_000, weight=10),
            PriceSegment(price_low=40_000, price_high=50_000, weight=30),
            PriceSegment(price_low=30_000, price_high=40_000, weight=40),
            PriceSegment(price_low=25_000, price_high=30_000, weight=20),
        ),
        time_segments=(TimeSegment(start_ts=_iso(0), end_ts=_iso(180), k_start=1.0, k_end=2.0),),
    )


@settings(max_examples=120)
@given(
    day=st.integers(min_value=0, max_value=180),
    price=st.floats(min_value=20_000, max_value=80_000, allow_nan=False, allow_infinity=False),
    mode=st.sampled_from(["bear", "bull"]),
)
def test_shares_are_bounded(day: int, price: float, mode: str) -> None:
    row = evaluate_point(_strategy(mode), _iso(day), price)

    assert 0 <= row.base_share <= 1
    assert 0 <= row.target_share <= 1


@settings(max_examples=120)
@given(
    p_a=st.floats(min_value=25_000, max_value=70_000, allow_nan=False, allow_infinity=False),
    p_b=st.floats(min_value=25_000, max_value=70_000, allow_nan=False, allow_infinity=False),
)
def test_monotonicity_by_favorable_price_direction(p_a: float, p_b: float) -> None:
    low, high = (p_a, p_b) if p_a <= p_b else (p_b, p_a)
    ts = _iso(60)

    bear = _strategy("bear")
    bull = _strategy("bull")

    bear_low = evaluate_point(bear, ts, low)
    bear_high = evaluate_point(bear, ts, high)
    assert bear_low.base_share >= bear_high.base_share

    bull_low = evaluate_point(bull, ts, low)
    bull_high = evaluate_point(bull, ts, high)
    assert bull_high.base_share >= bull_low.base_share


@settings(max_examples=120)
@given(
    day_a=st.integers(min_value=0, max_value=180),
    day_b=st.integers(min_value=0, max_value=180),
    mode=st.sampled_from(["bear", "bull"]),
)
def test_target_share_non_decreasing_over_time_with_non_decreasing_k(
    day_a: int,
    day_b: int,
    mode: str,
) -> None:
    left, right = (day_a, day_b) if day_a <= day_b else (day_b, day_a)
    strategy = _strategy(mode)
    price = 45_000.0

    first = evaluate_point(strategy, _iso(left), price)
    second = evaluate_point(strategy, _iso(right), price)

    assert second.target_share >= first.target_share
