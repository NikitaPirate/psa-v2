from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from psa_core.contracts import parse_strategy

from psa_cli.errors import CliDomainError, CliValidationError
from psa_cli.locks import exclusive_lock

STRATEGY_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _utc_now_iso() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _parse_iso_datetime(value: str, *, field_name: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CliValidationError(
            f"field '{field_name}' must be RFC3339 date-time"
        ) from exc


def _ensure_mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CliValidationError(f"{name} must be a JSON object")
    return value


def _validate_strategy_id(strategy_id: str) -> str:
    if not STRATEGY_ID_RE.match(strategy_id):
        raise CliValidationError(
            "strategy_id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
        )
    return strategy_id


def _store_root() -> Path:
    return Path.cwd() / ".psa" / "strategies"


def _strategy_dir(strategy_id: str) -> Path:
    return _store_root() / strategy_id


def _strategy_json_path(strategy_id: str) -> Path:
    return _strategy_dir(strategy_id) / "strategy.json"


def _log_ndjson_path(strategy_id: str) -> Path:
    return _strategy_dir(strategy_id) / "log.ndjson"


def _lock_path(strategy_id: str) -> Path:
    return _strategy_dir(strategy_id) / ".lock"


def _strategy_not_found(strategy_id: str) -> CliDomainError:
    return CliDomainError(
        "strategy_not_found",
        f"strategy '{strategy_id}' was not found",
        details={"strategy_id": strategy_id},
    )


def _read_json_file(path: Path) -> Mapping[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliDomainError(
            "storage_error",
            f"failed to read {path}",
            details={"path": str(path), "reason": exc.strerror or str(exc)},
        ) from exc

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CliDomainError(
            "storage_corrupted",
            f"file is not valid JSON: {path}",
            details={"path": str(path), "reason": exc.msg},
        ) from exc

    return _ensure_mapping(payload, name=str(path))


def _write_atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    text = json.dumps(payload, separators=(",", ":"), sort_keys=False) + "\n"
    try:
        with tmp_path.open("w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except OSError as exc:
        raise CliDomainError(
            "storage_error",
            f"failed to write {path}",
            details={"path": str(path), "reason": exc.strerror or str(exc)},
        ) from exc
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


def _load_strategy_record(strategy_id: str) -> Mapping[str, Any]:
    path = _strategy_json_path(strategy_id)
    if not path.is_file():
        raise _strategy_not_found(strategy_id)
    return _read_json_file(path)


def _load_logs(strategy_id: str) -> list[dict[str, Any]]:
    _load_strategy_record(strategy_id)
    log_path = _log_ndjson_path(strategy_id)
    if not log_path.is_file():
        return []

    rows: list[dict[str, Any]] = []
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CliDomainError(
            "storage_error",
            f"failed to read {log_path}",
            details={"path": str(log_path), "reason": exc.strerror or str(exc)},
        ) from exc

    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CliDomainError(
                "storage_corrupted",
                f"log line {idx + 1} is not valid JSON",
                details={"path": str(log_path), "line": idx + 1, "reason": exc.msg},
            ) from exc
        if not isinstance(payload, dict):
            raise CliDomainError(
                "storage_corrupted",
                f"log line {idx + 1} must be a JSON object",
                details={"path": str(log_path), "line": idx + 1},
            )
        rows.append(payload)
    return rows


def upsert_strategy(strategy_id: str, payload: Any) -> dict[str, Any]:
    _validate_strategy_id(strategy_id)
    strategy_payload = dict(_ensure_mapping(payload, name="strategy"))
    parse_strategy(strategy_payload)

    path = _strategy_json_path(strategy_id)
    with exclusive_lock(_lock_path(strategy_id)):
        now = _utc_now_iso()
        if path.is_file():
            current = _load_strategy_record(strategy_id)
            previous_strategy = current.get("strategy")
            previous_revision = current.get("revision")
            previous_updated_at = current.get("updated_at")

            if not isinstance(previous_revision, int) or previous_revision < 1:
                raise CliDomainError(
                    "storage_corrupted",
                    "strategy revision must be a positive integer",
                    details={"strategy_id": strategy_id, "path": str(path)},
                )
            if not isinstance(previous_updated_at, str):
                raise CliDomainError(
                    "storage_corrupted",
                    "strategy updated_at must be a string",
                    details={"strategy_id": strategy_id, "path": str(path)},
                )

            if previous_strategy == strategy_payload:
                return {
                    "strategy_id": strategy_id,
                    "result": "updated",
                    "revision": previous_revision,
                    "updated_at": previous_updated_at,
                }

            record = {
                "strategy_id": strategy_id,
                "revision": previous_revision + 1,
                "updated_at": now,
                "strategy": strategy_payload,
            }
            _write_atomic_json(path, record)
            return {
                "strategy_id": strategy_id,
                "result": "updated",
                "revision": record["revision"],
                "updated_at": record["updated_at"],
            }

        record = {
            "strategy_id": strategy_id,
            "revision": 1,
            "updated_at": now,
            "strategy": strategy_payload,
        }
        _write_atomic_json(path, record)
        return {
            "strategy_id": strategy_id,
            "result": "created",
            "revision": 1,
            "updated_at": now,
        }


def list_strategies() -> list[dict[str, Any]]:
    root = _store_root()
    if not root.exists():
        return []

    rows: list[dict[str, Any]] = []
    for strategy_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        path = strategy_dir / "strategy.json"
        if not path.is_file():
            continue
        record = _read_json_file(path)
        strategy_id = record.get("strategy_id")
        revision = record.get("revision")
        updated_at = record.get("updated_at")
        if not isinstance(strategy_id, str):
            raise CliDomainError(
                "storage_corrupted",
                "strategy_id must be a string",
                details={"path": str(path)},
            )
        if not isinstance(revision, int):
            raise CliDomainError(
                "storage_corrupted",
                "revision must be an integer",
                details={"path": str(path)},
            )
        if not isinstance(updated_at, str):
            raise CliDomainError(
                "storage_corrupted",
                "updated_at must be a string",
                details={"path": str(path)},
            )
        rows.append(
            {
                "strategy_id": strategy_id,
                "revision": revision,
                "updated_at": updated_at,
            }
        )
    return rows


def show_strategy(strategy_id: str) -> dict[str, Any]:
    _validate_strategy_id(strategy_id)
    record = dict(_load_strategy_record(strategy_id))
    record_strategy = record.get("strategy")
    _ensure_mapping(record_strategy, name="strategy")
    return record


def strategy_exists(strategy_id: str) -> bool:
    _validate_strategy_id(strategy_id)
    return _strategy_json_path(strategy_id).is_file()


def load_strategy_payload(strategy_id: str) -> Mapping[str, Any]:
    _validate_strategy_id(strategy_id)
    record = _load_strategy_record(strategy_id)
    strategy_payload = record.get("strategy")
    return _ensure_mapping(strategy_payload, name="strategy")


def append_log(strategy_id: str, payload: Any) -> dict[str, Any]:
    _validate_strategy_id(strategy_id)
    log_payload = dict(_ensure_mapping(payload, name="log payload"))
    ts = _utc_now_iso()
    log_id = uuid.uuid4().hex
    entry = {
        "log_id": log_id,
        "strategy_id": strategy_id,
        "ts": ts,
        "payload": log_payload,
    }
    serialized = json.dumps(entry, separators=(",", ":"), sort_keys=False) + "\n"

    with exclusive_lock(_lock_path(strategy_id)):
        _load_strategy_record(strategy_id)
        log_path = _log_ndjson_path(strategy_id)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise CliDomainError(
                "storage_error",
                f"failed to append log record for strategy '{strategy_id}'",
                details={"path": str(log_path), "reason": exc.strerror or str(exc)},
            ) from exc

    return {"log_id": log_id, "strategy_id": strategy_id, "ts": ts}


def list_logs(
    strategy_id: str,
    *,
    limit: int | None = None,
    from_ts: str | None = None,
    to_ts: str | None = None,
) -> list[dict[str, Any]]:
    _validate_strategy_id(strategy_id)
    if limit is not None and limit < 1:
        raise CliValidationError("limit must be >= 1")
    from_dt = _parse_iso_datetime(from_ts, field_name="from_ts") if from_ts else None
    to_dt = _parse_iso_datetime(to_ts, field_name="to_ts") if to_ts else None
    if from_dt and to_dt and from_dt > to_dt:
        raise CliValidationError("from_ts must be <= to_ts")

    rows = _load_logs(strategy_id)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        ts = row.get("ts")
        if not isinstance(ts, str):
            raise CliDomainError(
                "storage_corrupted",
                "log row must include string ts",
                details={"strategy_id": strategy_id},
            )
        ts_dt = _parse_iso_datetime(ts, field_name="ts")
        if from_dt and ts_dt < from_dt:
            continue
        if to_dt and ts_dt > to_dt:
            continue
        filtered.append(row)

    if limit is not None:
        return filtered[:limit]
    return filtered


def tail_logs(strategy_id: str, *, limit: int) -> list[dict[str, Any]]:
    _validate_strategy_id(strategy_id)
    if limit < 1:
        raise CliValidationError("limit must be >= 1")
    rows = _load_logs(strategy_id)
    if len(rows) <= limit:
        return rows
    return rows[-limit:]


def show_log(strategy_id: str, *, log_id: str) -> dict[str, Any]:
    _validate_strategy_id(strategy_id)
    if not log_id:
        raise CliValidationError("log_id must be non-empty")
    rows = _load_logs(strategy_id)
    for row in rows:
        if row.get("log_id") == log_id:
            return row
    raise CliDomainError(
        "log_not_found",
        f"log '{log_id}' was not found for strategy '{strategy_id}'",
        details={"strategy_id": strategy_id, "log_id": log_id},
    )
