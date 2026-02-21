from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - platform guard
    fcntl = None  # type: ignore[assignment]

SCHEMA_VERSION = "psa-memory.v1"


class StoreError(RuntimeError):
    pass


def default_memory_path() -> Path:
    return Path.cwd() / ".psa" / "psa-memory.v1.json"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}-{uuid.uuid4().hex[:8]}"


def _default_store() -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now,
        "user_profile": {
            "user_id": "default",
            "language": "auto",
            "philosophy": "",
            "constraints": [],
            "cli_runtime": {
                "mode": "tool",
                "package_name": "psa-strategy-cli",
                "command": "psa",
                "resolved": True,
                "updated_at": now,
            },
            "active_strategy_id": None,
            "updated_at": now,
        },
        "theses": {},
        "strategies": {},
        "strategy_versions": {},
        "strategy_thesis_links": [],
        "checkins": [],
        "decision_log": [],
    }


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _load_store(path: Path, *, create_if_missing: bool) -> tuple[dict[str, Any], bool]:
    if not path.exists():
        if not create_if_missing:
            raise StoreError(f"store_not_found: {path}")
        store = _default_store()
        _atomic_write_json(path, store)
        return store, True

    try:
        store = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StoreError(f"invalid_store_json: {exc}") from exc

    if not isinstance(store, dict):
        raise StoreError("invalid_store_shape: root must be object")

    _normalize_store(store)
    return store, False


def _normalize_store(store: dict[str, Any]) -> None:
    store.setdefault("schema_version", SCHEMA_VERSION)
    store.setdefault("updated_at", _utc_now())
    store.setdefault("user_profile", {})
    store.setdefault("theses", {})
    store.setdefault("strategies", {})
    store.setdefault("strategy_versions", {})
    store.setdefault("strategy_thesis_links", [])
    store.setdefault("checkins", [])
    store.setdefault("decision_log", [])

    if not isinstance(store["user_profile"], dict):
        store["user_profile"] = {}
    if not isinstance(store["theses"], dict):
        store["theses"] = {}
    if not isinstance(store["strategies"], dict):
        store["strategies"] = {}
    if not isinstance(store["strategy_versions"], dict):
        store["strategy_versions"] = {}
    if not isinstance(store["strategy_thesis_links"], list):
        store["strategy_thesis_links"] = []
    if not isinstance(store["checkins"], list):
        store["checkins"] = []
    if not isinstance(store["decision_log"], list):
        store["decision_log"] = []

    profile = store["user_profile"]
    profile.setdefault("user_id", "default")
    profile.setdefault("language", "auto")
    profile.setdefault("philosophy", "")
    profile.setdefault("constraints", [])
    profile.setdefault(
        "cli_runtime",
        {
            "mode": "tool",
            "package_name": "psa-strategy-cli",
            "command": "psa",
            "resolved": True,
            "updated_at": _utc_now(),
        },
    )
    profile.setdefault("active_strategy_id", None)
    profile.setdefault("updated_at", _utc_now())


def _require_object(payload: Any, field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        raise StoreError(f"invalid_payload: '{field}' must be an object")
    return value


def _require_strategy(store: dict[str, Any], strategy_id: str) -> dict[str, Any]:
    strategy = store["strategies"].get(strategy_id)
    if not isinstance(strategy, dict):
        raise StoreError(f"strategy_not_found: {strategy_id}")
    return strategy


def _require_thesis(store: dict[str, Any], thesis_id: str) -> dict[str, Any]:
    thesis = store["theses"].get(thesis_id)
    if not isinstance(thesis, dict):
        raise StoreError(f"thesis_not_found: {thesis_id}")
    return thesis


def _find_event_index(events: list[Any], event_id: str) -> int | None:
    for idx, item in enumerate(events):
        if isinstance(item, dict) and item.get("id") == event_id:
            return idx
    return None


def _validate_strategy_spec(spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise StoreError("invalid_strategy_spec: must be object")

    mode = spec.get("market_mode")
    if mode not in {"bear", "bull"}:
        raise StoreError("invalid_strategy_spec: market_mode must be bear or bull")

    price_segments = spec.get("price_segments")
    time_segments = spec.get("time_segments")
    if not isinstance(price_segments, list) or len(price_segments) == 0:
        raise StoreError("invalid_strategy_spec: price_segments must be non-empty list")
    if not isinstance(time_segments, list):
        raise StoreError("invalid_strategy_spec: time_segments must be list")

    return spec


def _op_upsert_profile(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    profile = _require_object(payload, "profile")
    store["user_profile"].update(profile)
    store["user_profile"]["updated_at"] = now
    store["updated_at"] = now
    return {"op": "upsert_profile", "profile": store["user_profile"]}


def _op_upsert_thesis(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    thesis = _require_object(payload, "thesis")
    thesis_id = thesis.get("id") or _new_id("thesis")
    existing = store["theses"].get(thesis_id, {})
    if not existing and not thesis.get("title"):
        raise StoreError("invalid_thesis: title is required for new thesis")

    merged = {
        "id": thesis_id,
        "title": thesis.get("title", existing.get("title", "")),
        "summary": thesis.get("summary", existing.get("summary", "")),
        "assumptions": thesis.get("assumptions", existing.get("assumptions", [])),
        "invalidation_signals": thesis.get(
            "invalidation_signals", existing.get("invalidation_signals", [])
        ),
        "horizon": thesis.get("horizon", existing.get("horizon", "")),
        "status": thesis.get("status", existing.get("status", "active")),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
    }

    store["theses"][thesis_id] = merged
    store["updated_at"] = now
    return {"op": "upsert_thesis", "thesis_id": thesis_id}


def _op_upsert_strategy(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    strategy = _require_object(payload, "strategy")
    strategy_id = strategy.get("id") or _new_id("strategy")
    existing = store["strategies"].get(strategy_id, {})
    strategy_name = strategy.get("name", strategy.get("title"))
    strategy_objective = strategy.get("objective", strategy.get("description", ""))
    strategy_notes = strategy.get("notes", strategy.get("comment", ""))

    if not existing and not strategy_name:
        raise StoreError("invalid_strategy: name is required for new strategy")

    merged = {
        "id": strategy_id,
        "name": strategy_name or existing.get("name", ""),
        "objective": strategy_objective or existing.get("objective", ""),
        "market_mode": strategy.get("market_mode", existing.get("market_mode", "bear")),
        "notes": strategy_notes or existing.get("notes", ""),
        "status": strategy.get("status", existing.get("status", "active")),
        "latest_version_id": existing.get("latest_version_id"),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
    }

    if merged["market_mode"] not in {"bear", "bull"}:
        raise StoreError("invalid_strategy: market_mode must be bear or bull")

    store["strategies"][strategy_id] = merged
    store["updated_at"] = now
    return {"op": "upsert_strategy", "strategy_id": strategy_id}


def _op_add_strategy_version(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    version = _require_object(payload, "version")
    strategy_id = version.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise StoreError("invalid_version: strategy_id is required")

    strategy = _require_strategy(store, strategy_id)
    spec = _validate_strategy_spec(version.get("strategy_spec"))

    version_id = version.get("id") or _new_id("version")
    record = {
        "id": version_id,
        "strategy_id": strategy_id,
        "label": version.get("label", ""),
        "rationale": version.get("rationale", ""),
        "created_by": version.get("created_by", "agent"),
        "created_at": now,
        "strategy_spec": spec,
        "tags": version.get("tags", []),
    }

    store["strategy_versions"][version_id] = record
    strategy["latest_version_id"] = version_id
    strategy["updated_at"] = now
    store["updated_at"] = now
    return {"op": "add_strategy_version", "strategy_id": strategy_id, "version_id": version_id}


def _op_link_strategy_thesis(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    link = payload.get("link", payload)
    if not isinstance(link, dict):
        raise StoreError("invalid_payload: 'link' must be an object")
    strategy_id = link.get("strategy_id")
    thesis_id = link.get("thesis_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise StoreError("invalid_link: strategy_id is required")
    if not isinstance(thesis_id, str) or not thesis_id:
        raise StoreError("invalid_link: thesis_id is required")

    _require_strategy(store, strategy_id)
    _require_thesis(store, thesis_id)

    existing_index: int | None = None
    for idx, item in enumerate(store["strategy_thesis_links"]):
        if (
            isinstance(item, dict)
            and item.get("strategy_id") == strategy_id
            and item.get("thesis_id") == thesis_id
        ):
            existing_index = idx
            break

    entry = {
        "strategy_id": strategy_id,
        "thesis_id": thesis_id,
        "rationale": link.get("rationale", ""),
        "created_at": now,
        "updated_at": now,
    }

    if existing_index is None:
        store["strategy_thesis_links"].append(entry)
    else:
        existing = store["strategy_thesis_links"][existing_index]
        if isinstance(existing, dict):
            entry["created_at"] = existing.get("created_at", now)
        store["strategy_thesis_links"][existing_index] = entry

    store["updated_at"] = now
    return {"op": "link_strategy_thesis", "strategy_id": strategy_id, "thesis_id": thesis_id}


def _op_set_active_strategy(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    strategy_id = payload.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise StoreError("invalid_payload: strategy_id is required")

    _require_strategy(store, strategy_id)
    store["user_profile"]["active_strategy_id"] = strategy_id
    store["user_profile"]["updated_at"] = now
    store["updated_at"] = now
    return {"op": "set_active_strategy", "strategy_id": strategy_id}


def _op_upsert_checkin(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    checkin = _require_object(payload, "checkin")
    strategy_id = checkin.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise StoreError("invalid_checkin: strategy_id is required")

    _require_strategy(store, strategy_id)
    checkin_raw_id = checkin.get("id")
    checkin_id = (
        checkin_raw_id if isinstance(checkin_raw_id, str) and checkin_raw_id else _new_id("checkin")
    )
    existing_index = _find_event_index(store["checkins"], checkin_id)
    existing = (
        store["checkins"][existing_index]
        if existing_index is not None and isinstance(store["checkins"][existing_index], dict)
        else {}
    )
    if existing and existing.get("strategy_id") != strategy_id:
        raise StoreError(f"checkin_conflict: {checkin_id}")

    record = {
        "id": checkin_id,
        "strategy_id": strategy_id,
        "timestamp": checkin.get("timestamp", existing.get("timestamp", now)),
        "price": checkin.get("price", existing.get("price")),
        "context": checkin.get("context", existing.get("context", "")),
        "evaluation": checkin.get("evaluation", existing.get("evaluation", {})),
        "note": checkin.get("note", existing.get("note", "")),
        "created_at": existing.get("created_at", now),
    }

    if existing_index is None:
        store["checkins"].append(record)
    else:
        store["checkins"][existing_index] = record
    store["updated_at"] = now
    return {"op": "upsert_checkin", "checkin_id": checkin_id, "strategy_id": strategy_id}


def _op_upsert_decision(store: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    decision = _require_object(payload, "decision")
    strategy_id = decision.get("strategy_id")
    if not isinstance(strategy_id, str) or not strategy_id:
        raise StoreError("invalid_decision: strategy_id is required")

    _require_strategy(store, strategy_id)
    decision_raw_id = decision.get("id")
    decision_id = (
        decision_raw_id
        if isinstance(decision_raw_id, str) and decision_raw_id
        else _new_id("decision")
    )
    existing_index = _find_event_index(store["decision_log"], decision_id)
    existing = (
        store["decision_log"][existing_index]
        if existing_index is not None and isinstance(store["decision_log"][existing_index], dict)
        else {}
    )
    if existing and existing.get("strategy_id") != strategy_id:
        raise StoreError(f"decision_conflict: {decision_id}")

    action_summary = decision.get("action_summary", existing.get("action_summary"))
    if not isinstance(action_summary, str) or not action_summary.strip():
        raise StoreError("invalid_decision: action_summary is required")

    record = {
        "id": decision_id,
        "strategy_id": strategy_id,
        "timestamp": decision.get("timestamp", existing.get("timestamp", now)),
        "action_summary": action_summary,
        "rationale": decision.get("rationale", existing.get("rationale", "")),
        "linked_checkin_id": decision.get(
            "linked_checkin_id",
            existing.get("linked_checkin_id"),
        ),
        "created_at": existing.get("created_at", now),
    }

    if existing_index is None:
        store["decision_log"].append(record)
    else:
        store["decision_log"][existing_index] = record
    store["updated_at"] = now
    return {"op": "upsert_decision", "decision_id": decision_id, "strategy_id": strategy_id}


def apply_operation(store: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any]:
    op_name = operation.get("op")
    if op_name == "upsert_profile":
        return _op_upsert_profile(store, operation)
    if op_name == "upsert_thesis":
        return _op_upsert_thesis(store, operation)
    if op_name == "upsert_strategy":
        return _op_upsert_strategy(store, operation)
    if op_name == "add_strategy_version":
        return _op_add_strategy_version(store, operation)
    if op_name == "link_strategy_thesis":
        return _op_link_strategy_thesis(store, operation)
    if op_name == "set_active_strategy":
        return _op_set_active_strategy(store, operation)
    if op_name in {"upsert_checkin", "add_checkin"}:
        return _op_upsert_checkin(store, operation)
    if op_name in {"upsert_decision", "add_decision"}:
        return _op_upsert_decision(store, operation)
    if op_name == "batch":
        items = operation.get("ops", operation.get("operations"))
        if not isinstance(items, list):
            raise StoreError("invalid_batch: ops or operations must be an array")
        results = []
        for item in items:
            if not isinstance(item, dict):
                raise StoreError("invalid_batch: each op must be an object")
            results.append(apply_operation(store, item))
        return {"op": "batch", "results": results}

    raise StoreError(f"unknown_operation: {op_name}")


def build_summary(store: dict[str, Any], strategy_id: str | None) -> dict[str, Any]:
    link_map: dict[str, list[str]] = {}
    for item in store["strategy_thesis_links"]:
        if not isinstance(item, dict):
            continue
        sid = item.get("strategy_id")
        tid = item.get("thesis_id")
        if isinstance(sid, str) and isinstance(tid, str):
            link_map.setdefault(sid, []).append(tid)

    checkin_last: dict[str, str] = {}
    for item in store["checkins"]:
        if not isinstance(item, dict):
            continue
        sid = item.get("strategy_id")
        ts = item.get("timestamp")
        if isinstance(sid, str) and isinstance(ts, str):
            if sid not in checkin_last or ts > checkin_last[sid]:
                checkin_last[sid] = ts

    decision_last: dict[str, str] = {}
    for item in store["decision_log"]:
        if not isinstance(item, dict):
            continue
        sid = item.get("strategy_id")
        ts = item.get("timestamp")
        if isinstance(sid, str) and isinstance(ts, str):
            if sid not in decision_last or ts > decision_last[sid]:
                decision_last[sid] = ts

    strategies_out = []
    for sid, strategy in sorted(store["strategies"].items()):
        if strategy_id and sid != strategy_id:
            continue
        if not isinstance(strategy, dict):
            continue
        strategies_out.append(
            {
                "id": sid,
                "name": strategy.get("name", ""),
                "status": strategy.get("status", "active"),
                "market_mode": strategy.get("market_mode", "bear"),
                "latest_version_id": strategy.get("latest_version_id"),
                "linked_thesis_ids": sorted(set(link_map.get(sid, []))),
                "last_checkin_at": checkin_last.get(sid),
                "last_decision_at": decision_last.get(sid),
                "updated_at": strategy.get("updated_at"),
            }
        )

    theses_out = []
    for tid, thesis in sorted(store["theses"].items()):
        if not isinstance(thesis, dict):
            continue
        theses_out.append(
            {
                "id": tid,
                "title": thesis.get("title", ""),
                "status": thesis.get("status", "active"),
                "updated_at": thesis.get("updated_at"),
            }
        )

    active_id = store.get("user_profile", {}).get("active_strategy_id")
    active_strategy = None
    if isinstance(active_id, str):
        active_strategy = store["strategies"].get(active_id)

    return {
        "schema_version": store.get("schema_version"),
        "updated_at": store.get("updated_at"),
        "user_profile": store.get("user_profile"),
        "active_strategy": {
            "id": active_id,
            "name": active_strategy.get("name") if isinstance(active_strategy, dict) else None,
            "latest_version_id": (
                active_strategy.get("latest_version_id")
                if isinstance(active_strategy, dict)
                else None
            ),
        },
        "counts": {
            "theses": len(store["theses"]),
            "strategies": len(store["strategies"]),
            "strategy_versions": len(store["strategy_versions"]),
            "strategy_thesis_links": len(store["strategy_thesis_links"]),
            "checkins": len(store["checkins"]),
            "decision_log": len(store["decision_log"]),
        },
        "theses": theses_out,
        "strategies": strategies_out,
    }


def validate_store_integrity(store: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    strategies = store["strategies"]
    theses = store["theses"]
    versions = store["strategy_versions"]

    active = store.get("user_profile", {}).get("active_strategy_id")
    if active is not None and active not in strategies:
        issues.append(f"active_strategy_missing: {active}")

    for vid, version in versions.items():
        if not isinstance(version, dict):
            issues.append(f"version_not_object: {vid}")
            continue
        sid = version.get("strategy_id")
        if sid not in strategies:
            issues.append(f"version_strategy_missing: {vid} -> {sid}")

    for sid, strategy in strategies.items():
        if not isinstance(strategy, dict):
            issues.append(f"strategy_not_object: {sid}")
            continue
        latest = strategy.get("latest_version_id")
        if latest is not None and latest not in versions:
            issues.append(f"strategy_latest_version_missing: {sid} -> {latest}")

    for link in store["strategy_thesis_links"]:
        if not isinstance(link, dict):
            issues.append("invalid_link_entry")
            continue
        sid = link.get("strategy_id")
        tid = link.get("thesis_id")
        if sid not in strategies:
            issues.append(f"link_strategy_missing: {sid}")
        if tid not in theses:
            issues.append(f"link_thesis_missing: {tid}")

    for checkin in store["checkins"]:
        if not isinstance(checkin, dict):
            issues.append("invalid_checkin_entry")
            continue
        sid = checkin.get("strategy_id")
        if sid not in strategies:
            issues.append(f"checkin_strategy_missing: {sid}")

    for decision in store["decision_log"]:
        if not isinstance(decision, dict):
            issues.append("invalid_decision_entry")
            continue
        sid = decision.get("strategy_id")
        if sid not in strategies:
            issues.append(f"decision_strategy_missing: {sid}")

    return issues


class MemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_memory_path()

    @property
    def lock_path(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".lock")

    def read(
        self,
        *,
        view: str = "summary",
        strategy_id: str | None = None,
        create_if_missing: bool = False,
    ) -> dict[str, Any]:
        store, _ = _load_store(self.path, create_if_missing=create_if_missing)
        if view == "full":
            return store
        return build_summary(store, strategy_id)

    def with_store(
        self,
        mutator: Callable[[dict[str, Any]], Any],
        *,
        create_if_missing: bool,
    ) -> dict[str, Any]:
        with _exclusive_lock(self.lock_path):
            store, _ = _load_store(self.path, create_if_missing=create_if_missing)
            result = mutator(store)
            _atomic_write_json(self.path, store)
            return {
                "result": result,
                "updated_at": store.get("updated_at"),
                "db_path": str(self.path),
            }

    def apply(self, operation: dict[str, Any], *, create_if_missing: bool = True) -> dict[str, Any]:
        return self.with_store(
            lambda store: apply_operation(store, operation),
            create_if_missing=create_if_missing,
        )

    def apply_batch(
        self,
        operations: list[dict[str, Any]],
        *,
        create_if_missing: bool = True,
    ) -> dict[str, Any]:
        return self.apply({"op": "batch", "ops": operations}, create_if_missing=create_if_missing)

    def validate(self) -> dict[str, Any]:
        store = self.read(view="full", create_if_missing=False)
        issues = validate_store_integrity(store)
        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues),
        }

    def get_strategy_spec_by_version(self, version_id: str) -> dict[str, Any]:
        store = self.read(view="full", create_if_missing=False)
        version = store.get("strategy_versions", {}).get(version_id)
        if not isinstance(version, dict):
            raise StoreError(f"version_not_found: {version_id}")

        spec = version.get("strategy_spec")
        if not isinstance(spec, dict):
            raise StoreError(f"strategy_spec_missing: {version_id}")
        return spec

    def get_latest_strategy_spec(
        self,
        *,
        strategy_id: str | None = None,
    ) -> tuple[dict[str, Any], str, str]:
        store = self.read(view="full", create_if_missing=False)
        strategies = store.get("strategies", {})
        if not isinstance(strategies, dict):
            raise StoreError("invalid_store_shape: strategies must be object")

        resolved_strategy_id = strategy_id
        if resolved_strategy_id is None:
            active_strategy_id = store.get("user_profile", {}).get("active_strategy_id")
            if isinstance(active_strategy_id, str) and active_strategy_id:
                resolved_strategy_id = active_strategy_id
            else:
                strategy_ids = [sid for sid, item in strategies.items() if isinstance(item, dict)]
                if len(strategy_ids) == 1:
                    resolved_strategy_id = strategy_ids[0]
                elif len(strategy_ids) == 0:
                    raise StoreError("strategy_not_found: no_strategies")
                else:
                    raise StoreError("active_strategy_required: multiple_strategies_present")

        strategy = strategies.get(resolved_strategy_id)
        if not isinstance(strategy, dict):
            raise StoreError(f"strategy_not_found: {resolved_strategy_id}")

        latest_version_id = strategy.get("latest_version_id")
        if not isinstance(latest_version_id, str) or not latest_version_id:
            raise StoreError(f"latest_version_missing: {resolved_strategy_id}")

        version = store.get("strategy_versions", {}).get(latest_version_id)
        if not isinstance(version, dict):
            raise StoreError(f"version_not_found: {latest_version_id}")

        spec = version.get("strategy_spec")
        if not isinstance(spec, dict):
            raise StoreError(f"strategy_spec_missing: {latest_version_id}")

        return spec, str(resolved_strategy_id), latest_version_id

    def get_full_store(self, *, create_if_missing: bool = False) -> dict[str, Any]:
        return self.read(view="full", create_if_missing=create_if_missing)


def store_error_code(exc: StoreError) -> str:
    text = str(exc)
    code, _, _ = text.partition(":")
    return code.strip().replace(" ", "_") or "store_error"
