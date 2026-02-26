from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

EVALUATE_POINT_REQUEST_SCHEMA = "evaluate_point.request.v1.json"
EVALUATE_PORTFOLIO_REQUEST_SCHEMA = "evaluate_portfolio.request.v1.json"
EVALUATE_ROWS_REQUEST_SCHEMA = "evaluate_rows.request.v1.json"
EVALUATE_ROWS_FROM_RANGES_REQUEST_SCHEMA = "evaluate_rows_from_ranges.request.v1.json"
STRATEGY_UPSERT_REQUEST_SCHEMA = "strategy_upsert.request.v1.json"

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMAS_DIR = _REPO_ROOT / "schemas"
_REQUEST_SCHEMA_FILES = (
    EVALUATE_POINT_REQUEST_SCHEMA,
    EVALUATE_PORTFOLIO_REQUEST_SCHEMA,
    EVALUATE_ROWS_REQUEST_SCHEMA,
    EVALUATE_ROWS_FROM_RANGES_REQUEST_SCHEMA,
    STRATEGY_UPSERT_REQUEST_SCHEMA,
)


@dataclass(slots=True)
class RequestSchemaValidator:
    validators: dict[str, Draft202012Validator]

    @classmethod
    def from_default_location(cls) -> RequestSchemaValidator:
        validators: dict[str, Draft202012Validator] = {}
        format_checker = FormatChecker()

        for schema_name in _REQUEST_SCHEMA_FILES:
            schema_path = _SCHEMAS_DIR / schema_name
            schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema_data)
            validators[schema_name] = Draft202012Validator(
                schema=schema_data,
                format_checker=format_checker,
            )

        return cls(validators=validators)

    def validate(self, payload: dict[str, Any], *, schema_name: str) -> None:
        if schema_name not in self.validators:
            raise RuntimeError(f"unknown request schema: {schema_name}")
        self.validators[schema_name].validate(payload)


_SCHEMA_VALIDATOR: RequestSchemaValidator | None = None


def initialize_request_schema_validator() -> None:
    global _SCHEMA_VALIDATOR
    if _SCHEMA_VALIDATOR is None:
        _SCHEMA_VALIDATOR = RequestSchemaValidator.from_default_location()


def validate_request_payload(payload: dict[str, Any], *, schema_name: str) -> None:
    initialize_request_schema_validator()
    assert _SCHEMA_VALIDATOR is not None
    _SCHEMA_VALIDATOR.validate(payload, schema_name=schema_name)


def validate_point_envelope(payload: dict[str, Any]) -> None:
    validate_request_payload(
        payload.get("strategy", {}),
        schema_name=STRATEGY_UPSERT_REQUEST_SCHEMA,
    )
    validate_request_payload(
        {
            "timestamp": payload.get("timestamp"),
            "price": payload.get("price"),
        },
        schema_name=EVALUATE_POINT_REQUEST_SCHEMA,
    )


def validate_rows_envelope(payload: dict[str, Any]) -> None:
    validate_request_payload(
        payload.get("strategy", {}),
        schema_name=STRATEGY_UPSERT_REQUEST_SCHEMA,
    )
    validate_request_payload(
        {"rows": payload.get("rows")},
        schema_name=EVALUATE_ROWS_REQUEST_SCHEMA,
    )


def validate_portfolio_envelope(payload: dict[str, Any]) -> None:
    validate_request_payload(
        payload.get("strategy", {}),
        schema_name=STRATEGY_UPSERT_REQUEST_SCHEMA,
    )
    portfolio_request = {
        key: payload[key]
        for key in ("timestamp", "price", "usd_amount", "asset_amount")
        if key in payload
    }
    for optional_key in (
        "avg_entry_price",
        "alignment_search_min_price",
        "alignment_search_max_price",
    ):
        if optional_key in payload:
            portfolio_request[optional_key] = payload[optional_key]
    validate_request_payload(
        portfolio_request,
        schema_name=EVALUATE_PORTFOLIO_REQUEST_SCHEMA,
    )


def validate_ranges_envelope(payload: dict[str, Any]) -> None:
    validate_request_payload(
        payload.get("strategy", {}),
        schema_name=STRATEGY_UPSERT_REQUEST_SCHEMA,
    )
    range_request = {
        key: payload[key]
        for key in (
            "price_start",
            "price_end",
            "price_steps",
            "time_start",
            "time_end",
            "time_steps",
        )
        if key in payload
    }
    if "include_price_breakpoints" in payload:
        range_request["include_price_breakpoints"] = payload["include_price_breakpoints"]
    validate_request_payload(
        range_request,
        schema_name=EVALUATE_ROWS_FROM_RANGES_REQUEST_SCHEMA,
    )
