from __future__ import annotations

import pytest
from psa_core.types import PriceSegment, StrategySpec, TimeSegment
from psa_core.validation import (
    validate_alignment_search_bounds,
    validate_observation,
    validate_portfolio_observation,
    validate_range_arguments,
    validate_strategy,
)


def test_rejects_overlapping_price_segments() -> None:
    strategy = StrategySpec(
        market_mode="bear",
        price_segments=(
            PriceSegment(price_low=40_000, price_high=50_000, weight=50),
            PriceSegment(price_low=49_000, price_high=60_000, weight=50),
        ),
    )

    with pytest.raises(ValueError, match="must not overlap"):
        validate_strategy(strategy)


def test_rejects_overlapping_time_segments() -> None:
    strategy = StrategySpec(
        market_mode="bull",
        price_segments=(PriceSegment(price_low=20_000, price_high=30_000, weight=100),),
        time_segments=(
            TimeSegment(
                start_ts="2026-01-01T00:00:00Z",
                end_ts="2026-03-01T00:00:00Z",
                k_start=1.0,
                k_end=1.1,
            ),
            TimeSegment(
                start_ts="2026-02-15T00:00:00Z",
                end_ts="2026-04-01T00:00:00Z",
                k_start=1.1,
                k_end=1.2,
            ),
        ),
    )

    with pytest.raises(ValueError, match="must not overlap"):
        validate_strategy(strategy)


def test_rejects_invalid_market_mode() -> None:
    strategy = StrategySpec(
        market_mode="bear",  # type: ignore[arg-type]
        price_segments=(PriceSegment(price_low=20_000, price_high=30_000, weight=100),),
    )

    assert validate_strategy(strategy) is None

    bad_strategy = StrategySpec(
        market_mode="sideways",  # type: ignore[arg-type]
        price_segments=(PriceSegment(price_low=20_000, price_high=30_000, weight=100),),
    )
    with pytest.raises(ValueError, match="market_mode"):
        validate_strategy(bad_strategy)


def test_rejects_all_zero_weights() -> None:
    strategy = StrategySpec(
        market_mode="bear",
        price_segments=(
            PriceSegment(price_low=20_000, price_high=30_000, weight=0),
            PriceSegment(price_low=30_000, price_high=40_000, weight=0),
        ),
    )

    with pytest.raises(ValueError, match="total weight must be > 0"):
        validate_strategy(strategy)


def test_validate_observation_rejects_bool_price() -> None:
    with pytest.raises(ValueError, match="price must be numeric"):
        validate_observation("2026-01-01T00:00:00Z", True)  # type: ignore[arg-type]


def test_validate_range_arguments_rejects_non_int_or_bool_steps() -> None:
    with pytest.raises(ValueError, match="price_steps must be an integer >= 1"):
        validate_range_arguments(
            price_start=60_000,
            price_end=25_000,
            price_steps=2.5,  # type: ignore[arg-type]
            time_start="2026-02-01T00:00:00Z",
            time_end="2026-04-01T00:00:00Z",
            time_steps=3,
        )

    with pytest.raises(ValueError, match="time_steps must be an integer >= 1"):
        validate_range_arguments(
            price_start=60_000,
            price_end=25_000,
            price_steps=3,
            time_start="2026-02-01T00:00:00Z",
            time_end="2026-04-01T00:00:00Z",
            time_steps=False,  # type: ignore[arg-type]
        )


def test_validate_portfolio_observation_rejects_empty_portfolio() -> None:
    with pytest.raises(ValueError, match="cannot both be zero"):
        validate_portfolio_observation(
            timestamp="2026-01-01T00:00:00Z",
            price=40_000,
            usd_amount=0,
            asset_amount=0,
            avg_entry_price=None,
        )


def test_validate_alignment_search_bounds_rejects_inverted_bounds() -> None:
    with pytest.raises(ValueError, match="must be <"):
        validate_alignment_search_bounds(min_price=100, max_price=50)
