from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jsonschema import ValidationError as JsonSchemaValidationError
from psa_core.contracts import ContractError


class ApiValidationError(ValueError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = [dict(item) for item in (details or [])]


class ApiLimitError(ApiValidationError):
    pass


def build_error_payload(
    *,
    code: str,
    message: str,
    details: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": [dict(item) for item in (details or [])],
        }
    }


def _stringify_location(location: Sequence[Any]) -> str:
    if not location:
        return "$"
    return ".".join(str(item) for item in location)


def _jsonschema_details(exc: JsonSchemaValidationError) -> list[dict[str, Any]]:
    path = "$"
    for item in exc.path:
        if isinstance(item, int):
            path += f"[{item}]"
        else:
            path += f".{item}"
    return [{"path": path, "validator": exc.validator, "message": exc.message}]


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiValidationError)
    async def _handle_api_validation_error(
        request: Request,
        exc: ApiValidationError,
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content=build_error_payload(code=exc.code, message=exc.message, details=exc.details),
        )

    @app.exception_handler(JsonSchemaValidationError)
    async def _handle_jsonschema_validation_error(
        request: Request,
        exc: JsonSchemaValidationError,
    ) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="schema_validation_error",
                message="Request payload does not match schema.",
                details=_jsonschema_details(exc),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        del request
        details = [
            {"path": _stringify_location(item.get("loc", ())), "message": item.get("msg", "")}
            for item in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="request_validation_error",
                message="Request payload is not valid JSON object.",
                details=details,
            ),
        )

    @app.exception_handler(ContractError)
    async def _handle_contract_error(request: Request, exc: ContractError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="contract_error",
                message=str(exc),
            ),
        )

    @app.exception_handler(ValueError)
    async def _handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=422,
            content=build_error_payload(
                code="validation_error",
                message=str(exc),
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=500,
            content=build_error_payload(
                code="internal_error",
                message="Internal server error.",
            ),
        )
