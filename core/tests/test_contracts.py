from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError, validate
from psa_core.contracts import (
    ContractError,
    evaluate_point_payload,
    evaluate_portfolio_payload,
    evaluate_rows_from_ranges_payload,
    evaluate_rows_payload,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples"
FORMAT_CHECKER = FormatChecker()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_files_are_valid() -> None:
    for schema_path in SCHEMAS.glob("*.json"):
        schema = _load_json(schema_path)
        Draft202012Validator.check_schema(schema)


def test_examples_match_request_schemas_and_produce_valid_responses() -> None:
    point_full_request = _load_json(EXAMPLES / "bear_accumulate_point.json")
    strategy_request_schema = _load_json(SCHEMAS / "strategy_upsert.request.v1.json")
    point_request_schema = _load_json(SCHEMAS / "evaluate_point.request.v1.json")
    point_response_schema = _load_json(SCHEMAS / "evaluate_point.response.v1.json")

    validate(point_full_request["strategy"], strategy_request_schema, format_checker=FORMAT_CHECKER)
    validate(
        {"timestamp": point_full_request["timestamp"], "price": point_full_request["price"]},
        point_request_schema,
        format_checker=FORMAT_CHECKER,
    )
    point_response = evaluate_point_payload(point_full_request)
    validate(point_response, point_response_schema, format_checker=FORMAT_CHECKER)

    rows_full_request = _load_json(EXAMPLES / "batch_timeseries_rows.json")
    rows_request_schema = _load_json(SCHEMAS / "evaluate_rows.request.v1.json")
    rows_response_schema = _load_json(SCHEMAS / "evaluate_rows.response.v1.json")

    validate(rows_full_request["strategy"], strategy_request_schema, format_checker=FORMAT_CHECKER)
    validate(
        {"rows": rows_full_request["rows"]},
        rows_request_schema,
        format_checker=FORMAT_CHECKER,
    )
    rows_response = evaluate_rows_payload(rows_full_request)
    validate(rows_response, rows_response_schema, format_checker=FORMAT_CHECKER)

    ranges_full_request = _load_json(EXAMPLES / "range_timeseries_rows.json")
    ranges_request_schema = _load_json(SCHEMAS / "evaluate_rows_from_ranges.request.v1.json")
    validate(
        ranges_full_request["strategy"],
        strategy_request_schema,
        format_checker=FORMAT_CHECKER,
    )
    ranges_request = {
        "price_start": ranges_full_request["price_start"],
        "price_end": ranges_full_request["price_end"],
        "price_steps": ranges_full_request["price_steps"],
        "time_start": ranges_full_request["time_start"],
        "time_end": ranges_full_request["time_end"],
        "time_steps": ranges_full_request["time_steps"],
        "include_price_breakpoints": ranges_full_request["include_price_breakpoints"],
    }
    validate(ranges_request, ranges_request_schema, format_checker=FORMAT_CHECKER)
    ranges_response = evaluate_rows_from_ranges_payload(ranges_full_request)
    validate(ranges_response, rows_response_schema, format_checker=FORMAT_CHECKER)

    portfolio_full_request = _load_json(EXAMPLES / "evaluate_portfolio.json")
    portfolio_request_schema = _load_json(SCHEMAS / "evaluate_portfolio.request.v1.json")
    portfolio_response_schema = _load_json(SCHEMAS / "evaluate_portfolio.response.v1.json")
    validate(
        portfolio_full_request["strategy"],
        strategy_request_schema,
        format_checker=FORMAT_CHECKER,
    )
    portfolio_request = {
        "timestamp": portfolio_full_request["timestamp"],
        "price": portfolio_full_request["price"],
        "usd_amount": portfolio_full_request["usd_amount"],
        "asset_amount": portfolio_full_request["asset_amount"],
        "avg_entry_price": portfolio_full_request["avg_entry_price"],
    }
    validate(portfolio_request, portfolio_request_schema, format_checker=FORMAT_CHECKER)
    portfolio_response = evaluate_portfolio_payload(portfolio_full_request)
    validate(portfolio_response, portfolio_response_schema, format_checker=FORMAT_CHECKER)


def test_schema_rejects_invalid_market_mode() -> None:
    schema = _load_json(SCHEMAS / "strategy_upsert.request.v1.json")
    strategy_payload = _load_json(EXAMPLES / "bear_accumulate_point.json")["strategy"]
    strategy_payload["market_mode"] = "sideways"

    with pytest.raises(ValidationError):
        validate(strategy_payload, schema, format_checker=FORMAT_CHECKER)


def test_schema_rejects_unknown_strategy_fields() -> None:
    schema = _load_json(SCHEMAS / "strategy_upsert.request.v1.json")
    strategy_payload = _load_json(EXAMPLES / "bear_accumulate_point.json")["strategy"]
    strategy_payload["unexpected_field"] = 0.2

    with pytest.raises(ValidationError):
        validate(strategy_payload, schema, format_checker=FORMAT_CHECKER)


def test_runtime_validation_rejects_overlapping_price_segments() -> None:
    request = _load_json(EXAMPLES / "bear_accumulate_point.json")
    request["strategy"]["price_segments"] = [
        {"price_low": 40_000, "price_high": 50_000, "weight": 50},
        {"price_low": 49_000, "price_high": 60_000, "weight": 50},
    ]

    with pytest.raises((ContractError, ValueError), match="overlap"):
        evaluate_point_payload(request)


def test_runtime_and_schema_reject_all_zero_weights() -> None:
    request_schema = _load_json(SCHEMAS / "strategy_upsert.request.v1.json")
    request = _load_json(EXAMPLES / "bear_accumulate_point.json")
    request["strategy"]["price_segments"] = [
        {"price_low": 40_000, "price_high": 50_000, "weight": 0},
        {"price_low": 50_000, "price_high": 60_000, "weight": 0},
    ]

    with pytest.raises(ValidationError):
        validate(request["strategy"], request_schema, format_checker=FORMAT_CHECKER)

    with pytest.raises((ContractError, ValueError), match="total weight must be > 0"):
        evaluate_point_payload(request)


def test_bull_example_matches_point_request_schema() -> None:
    schema = _load_json(SCHEMAS / "strategy_upsert.request.v1.json")
    payload = _load_json(EXAMPLES / "bull_distribute_point.json")["strategy"]
    validate(payload, schema, format_checker=FORMAT_CHECKER)


def test_rows_payload_matches_example_row_count() -> None:
    payload = _load_json(EXAMPLES / "batch_timeseries_rows.json")
    response = evaluate_rows_payload(payload)
    assert len(response["rows"]) == len(payload["rows"])


def test_ranges_payload_includes_breakpoints() -> None:
    payload = _load_json(EXAMPLES / "range_timeseries_rows.json")
    response = evaluate_rows_from_ranges_payload(payload)

    first_ts = response["rows"][0]["timestamp"]
    first_ts_prices = [row["price"] for row in response["rows"] if row["timestamp"] == first_ts]
    assert 50_000 in first_ts_prices
    assert 40_000 in first_ts_prices
    assert 30_000 in first_ts_prices


def test_ranges_payload_rejects_bool_steps_in_contract_adapter() -> None:
    payload = _load_json(EXAMPLES / "range_timeseries_rows.json")
    payload["price_steps"] = True

    with pytest.raises(ContractError, match="price_steps"):
        evaluate_rows_from_ranges_payload(payload)


def test_portfolio_payload_rejects_non_numeric_avg_entry_price() -> None:
    payload = _load_json(EXAMPLES / "evaluate_portfolio.json")
    payload["avg_entry_price"] = "oops"

    with pytest.raises(ContractError, match="avg_entry_price"):
        evaluate_portfolio_payload(payload)
