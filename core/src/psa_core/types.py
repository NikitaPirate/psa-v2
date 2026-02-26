from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MarketMode = Literal["bear", "bull"]


@dataclass(frozen=True, slots=True)
class PriceSegment:
    price_low: float
    price_high: float
    weight: float


@dataclass(frozen=True, slots=True)
class TimeSegment:
    start_ts: str
    end_ts: str
    k_start: float
    k_end: float


@dataclass(frozen=True, slots=True)
class StrategySpec:
    market_mode: MarketMode
    price_segments: tuple[PriceSegment, ...]
    time_segments: tuple[TimeSegment, ...] = ()


@dataclass(frozen=True, slots=True)
class ObservationRow:
    timestamp: str
    price: float


@dataclass(frozen=True, slots=True)
class EvaluationRow:
    timestamp: str
    price: float
    time_k: float
    virtual_price: float
    base_share: float
    target_share: float


@dataclass(frozen=True, slots=True)
class PortfolioObservation:
    timestamp: str
    price: float
    usd_amount: float
    asset_amount: float
    avg_entry_price: float | None = None
    alignment_search_min_price: float | None = None
    alignment_search_max_price: float | None = None


@dataclass(frozen=True, slots=True)
class PortfolioEvaluation:
    timestamp: str
    price: float
    time_k: float
    virtual_price: float
    base_share: float
    target_share: float
    share_deviation: float
    portfolio_value_usd: float
    asset_value_usd: float
    usd_value_usd: float
    target_asset_value_usd: float
    target_asset_amount: float
    asset_amount_delta: float
    usd_delta: float
    alignment_price: float | None
    avg_entry_price: float | None
    avg_entry_pnl_usd: float | None
    avg_entry_pnl_pct: float | None
