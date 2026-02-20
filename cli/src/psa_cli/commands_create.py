from __future__ import annotations

from copy import deepcopy
from typing import Any

from psa_cli.arg_types import parse_json_string
from psa_cli.errors import CliStateError, CliValidationError
from psa_cli.store import MemoryStore, StoreError, apply_operation


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _build_strategy_spec_from_args(args: Any) -> dict[str, Any]:
    if args.market_mode is None:
        raise CliValidationError(
            "--market-mode is required when --json is not provided",
            error_code="missing_market_mode",
        )
    if not args.price_segments:
        raise CliValidationError(
            "at least one --price-segment is required when --json is not provided",
            error_code="missing_price_segments",
        )
    return {
        "market_mode": args.market_mode,
        "price_segments": args.price_segments,
        "time_segments": args.time_segments or [],
    }


def apply_strategy_pack(
    store: MemoryStore,
    payload: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    if mode not in {"create", "update"}:
        raise CliValidationError(
            "invalid strategy-pack mode",
            error_code="invalid_strategy_pack_mode",
        )

    def _mutator(state: dict[str, Any]) -> dict[str, Any]:
        results: list[dict[str, Any]] = []

        thesis_input = payload.get("thesis")
        strategy_input = payload.get("strategy")
        version_input = payload.get("version")
        link_input = payload.get("link")
        checkin_input = payload.get("checkin")
        decision_input = payload.get("decision")
        set_active = bool(payload.get("set_active"))

        if mode == "create":
            if not isinstance(thesis_input, dict):
                raise StoreError("invalid_strategy_pack: thesis is required")
            if not isinstance(strategy_input, dict):
                raise StoreError("invalid_strategy_pack: strategy is required")
            if not isinstance(version_input, dict):
                raise StoreError("invalid_strategy_pack: version is required")

        if mode == "update" and not isinstance(version_input, dict):
            raise StoreError("invalid_strategy_pack: version is required")

        thesis_id: str | None = None
        if isinstance(thesis_input, dict):
            thesis_result = apply_operation(
                state,
                {"op": "upsert_thesis", "thesis": thesis_input},
            )
            results.append(thesis_result)
            thesis_id = thesis_result.get("thesis_id")

        strategy_id: str | None = None
        if isinstance(strategy_input, dict):
            strategy_result = apply_operation(
                state,
                {"op": "upsert_strategy", "strategy": strategy_input},
            )
            results.append(strategy_result)
            strategy_id = strategy_result.get("strategy_id")

        if strategy_id is None and isinstance(version_input, dict):
            sid = version_input.get("strategy_id")
            if isinstance(sid, str) and sid:
                strategy_id = sid

        if strategy_id is None:
            raise StoreError("invalid_strategy_pack: strategy_id cannot be resolved")

        if mode == "update" and strategy_id not in state.get("strategies", {}):
            raise StoreError(f"strategy_not_found: {strategy_id}")

        version_payload = deepcopy(version_input) if isinstance(version_input, dict) else {}
        if not version_payload.get("strategy_id"):
            version_payload["strategy_id"] = strategy_id
        version_result = apply_operation(
            state,
            {"op": "add_strategy_version", "version": version_payload},
        )
        results.append(version_result)
        version_id = version_result.get("version_id")

        link_rationale = ""
        if isinstance(link_input, dict):
            link_rationale = str(link_input.get("rationale", ""))
            if thesis_id is None:
                thesis_candidate = link_input.get("thesis_id")
                if isinstance(thesis_candidate, str) and thesis_candidate:
                    thesis_id = thesis_candidate

        if mode == "create" and thesis_id is None:
            raise StoreError("invalid_strategy_pack: thesis_id cannot be resolved")

        if thesis_id is not None:
            link_result = apply_operation(
                state,
                {
                    "op": "link_strategy_thesis",
                    "link": {
                        "strategy_id": strategy_id,
                        "thesis_id": thesis_id,
                        "rationale": link_rationale,
                    },
                },
            )
            results.append(link_result)

        if set_active:
            active_result = apply_operation(
                state,
                {
                    "op": "set_active_strategy",
                    "strategy_id": strategy_id,
                },
            )
            results.append(active_result)

        if isinstance(checkin_input, dict):
            checkin_payload = deepcopy(checkin_input)
            checkin_payload.setdefault("strategy_id", strategy_id)
            checkin_result = apply_operation(
                state,
                {
                    "op": "add_checkin",
                    "checkin": checkin_payload,
                },
            )
            results.append(checkin_result)

        if isinstance(decision_input, dict):
            decision_payload = deepcopy(decision_input)
            decision_payload.setdefault("strategy_id", strategy_id)
            decision_result = apply_operation(
                state,
                {
                    "op": "add_decision",
                    "decision": decision_payload,
                },
            )
            results.append(decision_result)

        return {
            "op": f"{mode}_strategy_pack",
            "strategy_id": strategy_id,
            "thesis_id": thesis_id,
            "version_id": version_id,
            "results": results,
        }

    return store.with_store(_mutator, create_if_missing=True)


def execute_create(args: Any, store: MemoryStore) -> dict[str, Any]:
    if args.create_command == "thesis":
        if args.json:
            payload = parse_json_string(args.json, field_name="--json")
        else:
            payload = _compact_dict(
                {
                    "id": args.id,
                    "title": args.title,
                    "summary": args.summary,
                    "assumptions": args.assumption if args.assumption is not None else None,
                    "invalidation_signals": (
                        args.invalidation_signal if args.invalidation_signal is not None else None
                    ),
                    "horizon": args.horizon,
                    "status": args.status,
                }
            )
        tx = store.apply({"op": "upsert_thesis", "thesis": payload}, create_if_missing=True)
        return {"command": "create thesis", **tx}

    if args.create_command == "strategy":
        if args.json:
            payload = parse_json_string(args.json, field_name="--json")
        else:
            payload = _compact_dict(
                {
                    "id": args.id,
                    "name": args.name,
                    "objective": args.objective,
                    "market_mode": args.market_mode,
                    "notes": args.notes,
                    "status": args.status,
                }
            )
        tx = store.apply({"op": "upsert_strategy", "strategy": payload}, create_if_missing=True)
        return {"command": "create strategy", **tx}

    if args.create_command == "version":
        if args.json:
            version_payload = parse_json_string(args.json, field_name="--json")
        else:
            version_payload = _compact_dict(
                {
                    "id": args.id,
                    "strategy_id": args.strategy_id,
                    "label": args.label,
                    "rationale": args.rationale,
                    "created_by": args.created_by,
                    "tags": args.tag if args.tag is not None else [],
                    "strategy_spec": _build_strategy_spec_from_args(args),
                }
            )
        tx = store.apply(
            {"op": "add_strategy_version", "version": version_payload},
            create_if_missing=False,
        )
        return {"command": "create version", **tx}

    if args.create_command == "link":
        tx = store.apply(
            {
                "op": "link_strategy_thesis",
                "link": {
                    "strategy_id": args.strategy_id,
                    "thesis_id": args.thesis_id,
                    "rationale": args.rationale,
                },
            },
            create_if_missing=False,
        )
        return {"command": "create link", **tx}

    if args.create_command == "checkin":
        evaluation = (
            parse_json_string(args.evaluation_json, field_name="--evaluation-json")
            if args.evaluation_json
            else {}
        )
        payload = _compact_dict(
            {
                "id": args.id,
                "strategy_id": args.strategy_id,
                "timestamp": args.timestamp,
                "price": args.price,
                "context": args.context,
                "evaluation": evaluation,
                "note": args.note,
            }
        )
        tx = store.apply({"op": "add_checkin", "checkin": payload}, create_if_missing=False)
        return {"command": "create checkin", **tx}

    if args.create_command == "decision":
        payload = _compact_dict(
            {
                "id": args.id,
                "strategy_id": args.strategy_id,
                "timestamp": args.timestamp,
                "action_summary": args.action_summary,
                "rationale": args.rationale,
                "linked_checkin_id": args.linked_checkin_id,
            }
        )
        tx = store.apply({"op": "add_decision", "decision": payload}, create_if_missing=False)
        return {"command": "create decision", **tx}

    if args.create_command == "strategy-pack":
        payload = parse_json_string(args.json, field_name="--json")
        tx = apply_strategy_pack(store, payload, mode="create")
        return {"command": "create strategy-pack", **tx}

    raise CliStateError(
        f"unsupported create command: {args.create_command}",
        error_code="unsupported_command",
    )
