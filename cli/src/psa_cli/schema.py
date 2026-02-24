from __future__ import annotations

import json
import os
import re
from datetime import datetime
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from psa_cli.errors import CliValidationError

REQUEST_SCHEMAS: dict[str, str] = {
    "evaluate-point": "evaluate_point.request.v1.json",
    "evaluate-rows": "evaluate_rows.request.v1.json",
    "evaluate-ranges": "evaluate_rows_from_ranges.request.v1.json",
    "strategy-upsert": "strategy_upsert.request.v1.json",
    "log-append": "log_append.request.v1.json",
}

FORMAT_CHECKER = FormatChecker()
RFC3339_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
PACKAGED_SCHEMA_ROOT = "psa_cli/schemas"


@FORMAT_CHECKER.checks("date-time")
def _is_rfc3339_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if not RFC3339_DATETIME_RE.match(value):
        return False

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def _schema_candidates() -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    env_dir = os.getenv("PSA_SCHEMA_DIR")
    if env_dir:
        candidates.append(("PSA_SCHEMA_DIR", Path(env_dir)))

    repo_root = Path(__file__).resolve().parents[3]
    candidates.append(("repo", repo_root / "schemas"))
    return candidates


@cache
def load_schema(schema_file: str) -> dict[str, Any]:
    checked: list[str] = []

    env_candidate: tuple[str, Path] | None = None
    repo_candidate: tuple[str, Path] | None = None
    for source_name, directory in _schema_candidates():
        if source_name == "PSA_SCHEMA_DIR":
            env_candidate = (source_name, directory)
        elif source_name == "repo":
            repo_candidate = (source_name, directory)

    if env_candidate is not None:
        _, directory = env_candidate
        checked.append(str(directory))
        path = directory / schema_file
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise CliValidationError(
                    f"failed to read schema '{schema_file}' from {path}: {exc.strerror or str(exc)}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise CliValidationError(
                    f"schema '{schema_file}' is not valid JSON: {exc.msg}"
                ) from exc

    checked.append(PACKAGED_SCHEMA_ROOT)
    packaged_path = files("psa_cli").joinpath("schemas", schema_file)
    if packaged_path.is_file():
        try:
            return json.loads(packaged_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CliValidationError(
                f"failed to read schema '{schema_file}' from {PACKAGED_SCHEMA_ROOT}: "
                f"{exc.strerror or str(exc)}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise CliValidationError(
                f"schema '{schema_file}' is not valid JSON: {exc.msg}"
            ) from exc

    if repo_candidate is not None:
        _, directory = repo_candidate
        checked.append(str(directory))
        path = directory / schema_file
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise CliValidationError(
                    f"failed to read schema '{schema_file}' from {path}: {exc.strerror or str(exc)}"
                ) from exc
            except json.JSONDecodeError as exc:
                raise CliValidationError(
                    f"schema '{schema_file}' is not valid JSON: {exc.msg}"
                ) from exc

    checked_locations = ", ".join(checked)
    raise CliValidationError(f"schema '{schema_file}' not found (checked: {checked_locations})")


def validate_request(command: str, payload: Any) -> None:
    schema_file = REQUEST_SCHEMAS.get(command)
    if schema_file is None:
        raise CliValidationError(f"unsupported command: {command}")

    schema = load_schema(schema_file)
    validator = Draft202012Validator(schema, format_checker=FORMAT_CHECKER)
    try:
        validator.validate(payload)
    except ValidationError as exc:
        raise CliValidationError(
            f"request does not match schema '{schema_file}': {exc.message}"
        ) from exc
