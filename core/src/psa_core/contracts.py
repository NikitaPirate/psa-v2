from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .engine import evaluate_point, evaluate_rows, evaluate_rows_from_ranges
from .types import EvaluationRow, ObservationRow, PriceSegment, StrategySpec, TimeSegment
from .validation import validate_strategy


class ContractError(ValueError):
    pass


def _ensure_mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{name} must be an object")
    return value


def _ensure_sequence(value: Any, *, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ContractError(f"{name} must be an array")
    return value


def _float_field(mapping: Mapping[str, Any], key: str) -> float:
    if key not in mapping:
        raise ContractError(f"missing required field: {key}")
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"field '{key}' must be numeric")
    return float(value)


def _str_field(mapping: Mapping[str, Any], key: str) -> str:
    if key not in mapping:
        raise ContractError(f"missing required field: {key}")
    value = mapping[key]
    if not isinstance(value, str):
        raise ContractError(f"field '{key}' must be a string")
    return value


def _int_field(mapping: Mapping[str, Any], key: str) -> int:
    if key not in mapping:
        raise ContractError(f"missing required field: {key}")
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"field '{key}' must be an integer")
    return int(value)


def _bool_field(mapping: Mapping[str, Any], key: str, default: bool) -> bool:
    if key not in mapping:
        return default
    value = mapping[key]
    if not isinstance(value, bool):
        raise ContractError(f"field '{key}' must be a boolean")
    return value


def parse_strategy(payload: Mapping[str, Any]) -> StrategySpec:
    obj = _ensure_mapping(payload, name="strategy")

    market_mode = _str_field(obj, "market_mode")

    raw_price_segments = _ensure_sequence(obj.get("price_segments"), name="price_segments")
    price_segments = tuple(
        PriceSegment(
            price_low=_float_field(
                _ensure_mapping(item, name=f"price_segments[{idx}]"),
                "price_low",
            ),
            price_high=_float_field(
                _ensure_mapping(item, name=f"price_segments[{idx}]"),
                "price_high",
            ),
            weight=_float_field(_ensure_mapping(item, name=f"price_segments[{idx}]"), "weight"),
        )
        for idx, item in enumerate(raw_price_segments)
    )

    raw_time_segments = _ensure_sequence(obj.get("time_segments", []), name="time_segments")
    time_segments = tuple(
        TimeSegment(
            start_ts=_str_field(_ensure_mapping(item, name=f"time_segments[{idx}]"), "start_ts"),
            end_ts=_str_field(_ensure_mapping(item, name=f"time_segments[{idx}]"), "end_ts"),
            k_start=_float_field(_ensure_mapping(item, name=f"time_segments[{idx}]"), "k_start"),
            k_end=_float_field(_ensure_mapping(item, name=f"time_segments[{idx}]"), "k_end"),
        )
        for idx, item in enumerate(raw_time_segments)
    )

    strategy = StrategySpec(
        market_mode=market_mode,  # type: ignore[arg-type]
        price_segments=price_segments,
        time_segments=time_segments,
    )
    validate_strategy(strategy)
    return strategy


def parse_observation_row(payload: Mapping[str, Any]) -> ObservationRow:
    obj = _ensure_mapping(payload, name="row")
    return ObservationRow(timestamp=_str_field(obj, "timestamp"), price=_float_field(obj, "price"))


def read_evaluate_point_request(payload: Mapping[str, Any]) -> tuple[StrategySpec, ObservationRow]:
    obj = _ensure_mapping(payload, name="request")
    strategy = parse_strategy(_ensure_mapping(obj.get("strategy"), name="strategy"))
    row = ObservationRow(timestamp=_str_field(obj, "timestamp"), price=_float_field(obj, "price"))
    return strategy, row


def read_evaluate_rows_request(
    payload: Mapping[str, Any],
) -> tuple[StrategySpec, list[ObservationRow]]:
    obj = _ensure_mapping(payload, name="request")
    strategy = parse_strategy(_ensure_mapping(obj.get("strategy"), name="strategy"))

    raw_rows = _ensure_sequence(obj.get("rows"), name="rows")
    rows = [
        parse_observation_row(_ensure_mapping(item, name=f"rows[{idx}]"))
        for idx, item in enumerate(raw_rows)
    ]
    return strategy, rows


def read_evaluate_rows_ranges_request(
    payload: Mapping[str, Any],
) -> tuple[StrategySpec, dict[str, Any]]:
    obj = _ensure_mapping(payload, name="request")
    strategy = parse_strategy(_ensure_mapping(obj.get("strategy"), name="strategy"))

    params = {
        "price_start": _float_field(obj, "price_start"),
        "price_end": _float_field(obj, "price_end"),
        "price_steps": _int_field(obj, "price_steps"),
        "time_start": _str_field(obj, "time_start"),
        "time_end": _str_field(obj, "time_end"),
        "time_steps": _int_field(obj, "time_steps"),
        "include_price_breakpoints": _bool_field(obj, "include_price_breakpoints", True),
    }
    return strategy, params


def row_to_dict(row: EvaluationRow) -> dict[str, Any]:
    return {
        "timestamp": row.timestamp,
        "price": row.price,
        "time_k": row.time_k,
        "virtual_price": row.virtual_price,
        "base_share": row.base_share,
        "target_share": row.target_share,
    }


def evaluate_point_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    strategy, row = read_evaluate_point_request(payload)
    evaluated = evaluate_point(strategy=strategy, timestamp=row.timestamp, price=row.price)
    return {"row": row_to_dict(evaluated)}


def evaluate_rows_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    strategy, rows = read_evaluate_rows_request(payload)
    evaluated = evaluate_rows(strategy=strategy, rows=rows)
    return {"rows": [row_to_dict(row) for row in evaluated]}


def evaluate_rows_from_ranges_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    strategy, params = read_evaluate_rows_ranges_request(payload)
    evaluated = evaluate_rows_from_ranges(strategy=strategy, **params)
    return {"rows": [row_to_dict(row) for row in evaluated]}
