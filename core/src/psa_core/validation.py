from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime

from psa_core.types import MarketMode, PriceSegment, StrategySpec, TimeSegment

_ALLOWED_MARKET_MODES: set[str] = {"bear", "bull"}

# Validation scope:
# - This module owns semantic validation for domain objects and API-level parameters.
# - Raw payload shape/type parsing is handled in contracts.py.
# - Math routines in engine.py/math.py assume these semantic preconditions are already met.


def parse_iso8601_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty ISO-8601 string")

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone info")
    return parsed


def _require_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def _require_positive(name: str, value: float) -> None:
    _require_finite(name, value)
    if float(value) <= 0:
        raise ValueError(f"{name} must be > 0")


def _validate_steps(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer >= 1")
    if value < 1:
        raise ValueError(f"{name} must be an integer >= 1")


def validate_price_segments(segments: Iterable[PriceSegment]) -> None:
    items = list(segments)
    if len(items) == 0:
        raise ValueError("price_segments must contain at least one segment")

    for idx, segment in enumerate(items):
        _require_finite(f"price_segments[{idx}].price_low", segment.price_low)
        _require_finite(f"price_segments[{idx}].price_high", segment.price_high)
        _require_finite(f"price_segments[{idx}].weight", segment.weight)

        if segment.price_low >= segment.price_high:
            raise ValueError(f"price_segments[{idx}] must satisfy price_low < price_high")
        if segment.weight < 0:
            raise ValueError(f"price_segments[{idx}].weight must be >= 0")

    total_weight = sum(float(segment.weight) for segment in items)
    if total_weight <= 0:
        raise ValueError("price_segments total weight must be > 0")

    sorted_by_low = sorted(items, key=lambda item: item.price_low)
    for prev, current in zip(sorted_by_low, sorted_by_low[1:], strict=False):
        if current.price_low < prev.price_high:
            raise ValueError("price_segments must not overlap")


def validate_time_segments(segments: Iterable[TimeSegment]) -> None:
    items = list(segments)
    if not items:
        return

    parsed_pairs: list[tuple[datetime, datetime]] = []
    for idx, segment in enumerate(items):
        start = parse_iso8601_utc(segment.start_ts)
        end = parse_iso8601_utc(segment.end_ts)
        if start >= end:
            raise ValueError(f"time_segments[{idx}] must satisfy start_ts < end_ts")

        _require_finite(f"time_segments[{idx}].k_start", segment.k_start)
        _require_finite(f"time_segments[{idx}].k_end", segment.k_end)
        if segment.k_start <= 0 or segment.k_end <= 0:
            raise ValueError(f"time_segments[{idx}] requires k_start > 0 and k_end > 0")
        parsed_pairs.append((start, end))

    indexed = sorted(enumerate(parsed_pairs), key=lambda item: item[1][0])
    for (_, (_, prev_end)), (_, (current_start, _)) in zip(indexed, indexed[1:], strict=False):
        if current_start < prev_end:
            raise ValueError("time_segments must not overlap")


def validate_market_mode(mode: MarketMode) -> None:
    if mode not in _ALLOWED_MARKET_MODES:
        raise ValueError("market_mode must be one of {'bear', 'bull'}")


def validate_strategy(strategy: StrategySpec) -> None:
    validate_market_mode(strategy.market_mode)
    validate_price_segments(strategy.price_segments)
    validate_time_segments(strategy.time_segments)


def validate_observation(timestamp: str, price: float) -> None:
    parse_iso8601_utc(timestamp)
    _require_positive("price", price)


def validate_range_arguments(
    *,
    price_start: float,
    price_end: float,
    price_steps: int,
    time_start: str,
    time_end: str,
    time_steps: int,
) -> tuple[datetime, datetime]:
    _require_positive("price_start", price_start)
    _require_positive("price_end", price_end)
    _validate_steps("price_steps", price_steps)
    _validate_steps("time_steps", time_steps)

    start_ts = parse_iso8601_utc(time_start)
    end_ts = parse_iso8601_utc(time_end)
    return start_ts, end_ts
