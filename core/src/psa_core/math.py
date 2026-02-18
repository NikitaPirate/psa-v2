from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from psa_core.types import MarketMode, PriceSegment, TimeSegment
from psa_core.validation import parse_iso8601_utc

EPS = 1e-12


def clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def normalize_weights(segments: Sequence[PriceSegment]) -> list[float]:
    # Precondition: segments were validated, including total weight > 0.
    weights = [float(segment.weight) for segment in segments]
    total = sum(weights)
    return [weight / total for weight in weights]


def compute_price_share(
    price: float,
    segments: Sequence[PriceSegment],
    market_mode: MarketMode,
) -> float:
    normalized = normalize_weights(segments)

    share = 0.0
    for segment, weight in zip(segments, normalized, strict=True):
        low = float(segment.price_low)
        high = float(segment.price_high)
        width = max(high - low, EPS)

        if market_mode == "bear":
            if price >= high:
                local = 0.0
            elif price <= low:
                local = 1.0
            else:
                local = (high - price) / width
        else:
            if price <= low:
                local = 0.0
            elif price >= high:
                local = 1.0
            else:
                local = (price - low) / width

        share += weight * clamp(local, 0.0, 1.0)

    return clamp(share, 0.0, 1.0)


def _segment_k(segment: TimeSegment, ts: datetime) -> float | None:
    start = parse_iso8601_utc(segment.start_ts)
    end = parse_iso8601_utc(segment.end_ts)

    if ts < start or ts > end:
        return None

    span = (end - start).total_seconds()
    if span <= EPS:
        return float(segment.k_end)

    elapsed = (ts - start).total_seconds()
    ratio = clamp(elapsed / span, 0.0, 1.0)
    return float(segment.k_start + (segment.k_end - segment.k_start) * ratio)


def compute_time_coefficient(timestamp: str, segments: Sequence[TimeSegment]) -> float:
    if len(segments) == 0:
        return 1.0

    ts = parse_iso8601_utc(timestamp)
    ordered = sorted(segments, key=lambda item: parse_iso8601_utc(item.start_ts))

    inside = next(
        (value for value in (_segment_k(segment, ts) for segment in ordered) if value is not None),
        None,
    )
    if inside is not None:
        return max(float(inside), EPS)

    first_start = parse_iso8601_utc(ordered[0].start_ts)
    if ts < first_start:
        return max(float(ordered[0].k_start), EPS)

    last = ordered[-1]
    last_end = parse_iso8601_utc(last.end_ts)
    if ts > last_end:
        return max(float(last.k_end), EPS)

    for left, right in zip(ordered, ordered[1:], strict=False):
        left_end = parse_iso8601_utc(left.end_ts)
        right_start = parse_iso8601_utc(right.start_ts)
        if left_end < ts < right_start:
            return max(float(left.k_end), EPS)

    return 1.0


def compute_virtual_price(price: float, time_k: float, market_mode: MarketMode) -> float:
    safe_k = max(time_k, EPS)
    if market_mode == "bear":
        return price / safe_k
    return price * safe_k
