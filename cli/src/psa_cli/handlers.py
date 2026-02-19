from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from psa_core.contracts import (
    evaluate_point_payload,
    evaluate_rows_from_ranges_payload,
    evaluate_rows_payload,
)

from psa_cli.errors import CliValidationError

COMMAND_HANDLERS = {
    "evaluate-point": evaluate_point_payload,
    "evaluate-rows": evaluate_rows_payload,
    "evaluate-ranges": evaluate_rows_from_ranges_payload,
}


def execute_command(command: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise CliValidationError("request payload must be a JSON object")

    handler = COMMAND_HANDLERS.get(command)
    if handler is None:
        raise CliValidationError(f"unsupported command: {command}")

    return handler(payload)
