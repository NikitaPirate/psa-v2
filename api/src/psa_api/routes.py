from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from psa_core.contracts import (
    evaluate_point_payload,
    evaluate_portfolio_payload,
    evaluate_rows_from_ranges_payload,
    evaluate_rows_payload,
)

from psa_api.errors import ApiLimitError
from psa_api.schema_validation import (
    validate_point_envelope,
    validate_portfolio_envelope,
    validate_ranges_envelope,
    validate_rows_envelope,
)

router = APIRouter(prefix="/v1", tags=["v1"])

MAX_EVALUATION_ROWS = 10_000
CLI_HINT = "For larger batch jobs, use the CLI workflow."


@router.post("/evaluate/point")
async def evaluate_point_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    validate_point_envelope(payload)
    return evaluate_point_payload(payload)


@router.post("/evaluate/portfolio")
async def evaluate_portfolio_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    validate_portfolio_envelope(payload)
    return evaluate_portfolio_payload(payload)


@router.post("/evaluate/rows")
async def evaluate_rows_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    validate_rows_envelope(payload)

    rows = payload.get("rows", [])
    row_count = len(rows)
    if row_count > MAX_EVALUATION_ROWS:
        raise ApiLimitError(
            code="rows_limit_exceeded",
            message=(
                f"rows length must be <= {MAX_EVALUATION_ROWS}. Received {row_count}. {CLI_HINT}"
            ),
            details=[{"field": "rows", "actual": row_count, "limit": MAX_EVALUATION_ROWS}],
        )

    return evaluate_rows_payload(payload)


@router.post("/evaluate/rows-from-ranges")
async def evaluate_rows_from_ranges_endpoint(payload: dict[str, Any]) -> dict[str, Any]:
    validate_ranges_envelope(payload)

    price_steps = int(payload["price_steps"])
    time_steps = int(payload["time_steps"])
    requested_rows = price_steps * time_steps
    if requested_rows > MAX_EVALUATION_ROWS:
        raise ApiLimitError(
            code="ranges_limit_exceeded",
            message=(
                "price_steps * time_steps must be <= "
                f"{MAX_EVALUATION_ROWS}. Received {requested_rows}. {CLI_HINT}"
            ),
            details=[
                {
                    "field": "price_steps*time_steps",
                    "actual": requested_rows,
                    "limit": MAX_EVALUATION_ROWS,
                }
            ],
        )

    return evaluate_rows_from_ranges_payload(payload)
