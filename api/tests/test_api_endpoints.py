from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import psa_api.routes as api_routes
import pytest
from fastapi.testclient import TestClient
from jsonschema import FormatChecker, validate
from psa_api.main import app

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples"
FORMAT_CHECKER = FormatChecker()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_error_shape(payload: dict[str, Any]) -> None:
    assert set(payload) == {"error"}
    error = payload["error"]
    assert isinstance(error, dict)
    assert "code" in error
    assert "message" in error
    assert "details" in error
    assert isinstance(error["details"], list)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_evaluate_point_success_matches_response_schema(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "bear_accumulate_point.json")
    response = client.post("/v1/evaluate/point", json=payload)
    assert response.status_code == 200

    schema = _load_json(SCHEMAS / "evaluate_point.response.v1.json")
    validate(response.json(), schema, format_checker=FORMAT_CHECKER)


def test_evaluate_rows_success_matches_response_schema(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "batch_timeseries_rows.json")
    response = client.post("/v1/evaluate/rows", json=payload)
    assert response.status_code == 200

    schema = _load_json(SCHEMAS / "evaluate_rows.response.v1.json")
    validate(response.json(), schema, format_checker=FORMAT_CHECKER)


def test_evaluate_portfolio_success_matches_response_schema(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "evaluate_portfolio.json")
    response = client.post("/v1/evaluate/portfolio", json=payload)
    assert response.status_code == 200

    schema = _load_json(SCHEMAS / "evaluate_portfolio.response.v1.json")
    validate(response.json(), schema, format_checker=FORMAT_CHECKER)


def test_evaluate_rows_from_ranges_success_matches_response_schema(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "range_timeseries_rows.json")
    response = client.post("/v1/evaluate/rows-from-ranges", json=payload)
    assert response.status_code == 200

    schema = _load_json(SCHEMAS / "evaluate_rows.response.v1.json")
    validate(response.json(), schema, format_checker=FORMAT_CHECKER)


def test_schema_error_returns_unified_422(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "bear_accumulate_point.json")
    payload["strategy"]["unexpected_field"] = 1

    response = client.post("/v1/evaluate/point", json=payload)
    assert response.status_code == 422
    body = response.json()
    _assert_error_shape(body)
    assert body["error"]["code"] == "schema_validation_error"


def test_runtime_semantic_error_returns_unified_422(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "bear_accumulate_point.json")
    payload["strategy"]["price_segments"] = [
        {"price_low": 40_000, "price_high": 50_000, "weight": 50},
        {"price_low": 49_000, "price_high": 60_000, "weight": 50},
    ]

    response = client.post("/v1/evaluate/point", json=payload)
    assert response.status_code == 422
    body = response.json()
    _assert_error_shape(body)
    assert body["error"]["code"] == "validation_error"
    assert "overlap" in body["error"]["message"]


def test_portfolio_runtime_semantic_error_returns_unified_422(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "evaluate_portfolio.json")
    payload["usd_amount"] = 0
    payload["asset_amount"] = 0

    response = client.post("/v1/evaluate/portfolio", json=payload)
    assert response.status_code == 422
    body = response.json()
    _assert_error_shape(body)
    assert body["error"]["code"] == "validation_error"
    assert "cannot both be zero" in body["error"]["message"]


def test_rows_limit_returns_422_with_cli_hint(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "batch_timeseries_rows.json")
    payload["rows"] = [{"timestamp": "2026-03-01T00:00:00Z", "price": 42_000}] * 10_001

    response = client.post("/v1/evaluate/rows", json=payload)
    assert response.status_code == 422
    body = response.json()
    _assert_error_shape(body)
    assert body["error"]["code"] == "rows_limit_exceeded"
    assert "CLI workflow" in body["error"]["message"]


def test_ranges_limit_returns_422_with_cli_hint(client: TestClient) -> None:
    payload = _load_json(EXAMPLES / "range_timeseries_rows.json")
    payload["price_steps"] = 101
    payload["time_steps"] = 100

    response = client.post("/v1/evaluate/rows-from-ranges", json=payload)
    assert response.status_code == 422
    body = response.json()
    _assert_error_shape(body)
    assert body["error"]["code"] == "ranges_limit_exceeded"
    assert "CLI workflow" in body["error"]["message"]


def test_unexpected_error_returns_unified_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_unexpected(payload: dict[str, Any]) -> dict[str, Any]:
        del payload
        raise RuntimeError("unexpected")

    monkeypatch.setattr(api_routes, "evaluate_point_payload", _raise_unexpected)
    payload = _load_json(EXAMPLES / "bear_accumulate_point.json")

    response = client.post("/v1/evaluate/point", json=payload)
    assert response.status_code == 500
    body = response.json()
    _assert_error_shape(body)
    assert body["error"]["code"] == "internal_error"


def test_openapi_contains_v1_evaluate_paths(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/v1/evaluate/point" in paths
    assert "/v1/evaluate/portfolio" in paths
    assert "/v1/evaluate/rows" in paths
    assert "/v1/evaluate/rows-from-ranges" in paths
