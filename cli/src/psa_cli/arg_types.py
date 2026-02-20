from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from psa_cli.errors import CliValidationError

RFC3339_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
TIME_SEGMENT_RE = re.compile(
    r"^(?P<start>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})):"
    r"(?P<end>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})):"
    r"(?P<k_start>-?\d+(?:\.\d+)?):(?P<k_end>-?\d+(?:\.\d+)?)$"
)


def parse_json_string(raw: str, *, field_name: str = "json") -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliValidationError(
            f"invalid JSON in {field_name}: {exc.msg}",
            error_code="invalid_json",
        ) from exc

    if not isinstance(payload, dict):
        raise CliValidationError(
            f"{field_name} must be a JSON object",
            error_code="invalid_json_shape",
        )
    return payload


def _ensure_datetime(value: str, *, field_name: str) -> str:
    if not RFC3339_DATETIME_RE.match(value):
        raise CliValidationError(
            f"invalid {field_name}: expected RFC3339 date-time with timezone",
            error_code="invalid_datetime",
        )

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CliValidationError(
            f"invalid {field_name}: {value}",
            error_code="invalid_datetime",
        ) from exc

    return value


def parse_price_segment(raw: str) -> dict[str, float]:
    parts = raw.split(":")
    if len(parts) != 3:
        raise CliValidationError(
            "invalid --price-segment, expected low:high:weight",
            error_code="invalid_price_segment",
        )
    try:
        low = float(parts[0])
        high = float(parts[1])
        weight = float(parts[2])
    except ValueError as exc:
        raise CliValidationError(
            "invalid --price-segment numeric values",
            error_code="invalid_price_segment",
        ) from exc

    return {"price_low": low, "price_high": high, "weight": weight}


def parse_time_segment(raw: str) -> dict[str, Any]:
    match = TIME_SEGMENT_RE.match(raw)
    if match is None:
        raise CliValidationError(
            "invalid --time-segment, expected start:end:k_start:k_end",
            error_code="invalid_time_segment",
        )

    start = _ensure_datetime(match.group("start"), field_name="time-segment.start")
    end = _ensure_datetime(match.group("end"), field_name="time-segment.end")
    return {
        "start_ts": start,
        "end_ts": end,
        "k_start": float(match.group("k_start")),
        "k_end": float(match.group("k_end")),
    }


def parse_row(raw: str) -> dict[str, Any]:
    try:
        ts, price_raw = raw.rsplit(":", maxsplit=1)
    except ValueError as exc:
        raise CliValidationError(
            "invalid --row, expected timestamp:price",
            error_code="invalid_row",
        ) from exc

    timestamp = _ensure_datetime(ts, field_name="row.timestamp")
    try:
        price = float(price_raw)
    except ValueError as exc:
        raise CliValidationError(
            "invalid --row price",
            error_code="invalid_row",
        ) from exc

    return {"timestamp": timestamp, "price": price}


def ensure_datetime(value: str, *, field_name: str) -> str:
    return _ensure_datetime(value, field_name=field_name)
