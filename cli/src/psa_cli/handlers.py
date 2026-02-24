from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from psa_core.contracts import (
    evaluate_point_payload,
    evaluate_rows_from_ranges_payload,
    evaluate_rows_payload,
)

from psa_cli.errors import CliValidationError
from psa_cli.skills import install_skill
from psa_cli.store import (
    append_log,
    list_logs,
    list_strategies,
    load_strategy_payload,
    show_log,
    show_strategy,
    strategy_exists,
    tail_logs,
    upsert_strategy,
)


def _ensure_mapping(value: Any, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CliValidationError(f"{name} must be a JSON object")
    return value


def _evaluate_point_with_saved_strategy(strategy_id: str, payload: Any) -> dict[str, Any]:
    request = dict(_ensure_mapping(payload, name="request"))
    request["strategy"] = dict(load_strategy_payload(strategy_id))
    return evaluate_point_payload(request)


def _evaluate_rows_with_saved_strategy(strategy_id: str, payload: Any) -> dict[str, Any]:
    request = dict(_ensure_mapping(payload, name="request"))
    request["strategy"] = dict(load_strategy_payload(strategy_id))
    return evaluate_rows_payload(request)


def _evaluate_ranges_with_saved_strategy(strategy_id: str, payload: Any) -> dict[str, Any]:
    request = dict(_ensure_mapping(payload, name="request"))
    request["strategy"] = dict(load_strategy_payload(strategy_id))
    return evaluate_rows_from_ranges_payload(request)


def execute_command(command: str, payload: Any, *, args: Any) -> dict[str, Any]:
    if command == "evaluate-point":
        return _evaluate_point_with_saved_strategy(args.strategy_id, payload)
    if command == "evaluate-rows":
        return _evaluate_rows_with_saved_strategy(args.strategy_id, payload)
    if command == "evaluate-ranges":
        return _evaluate_ranges_with_saved_strategy(args.strategy_id, payload)
    if command == "strategy-upsert":
        return upsert_strategy(args.strategy_id, payload)
    if command == "strategy-list":
        return {"strategies": list_strategies()}
    if command == "strategy-show":
        return show_strategy(args.strategy_id)
    if command == "strategy-exists":
        return {"strategy_id": args.strategy_id, "exists": strategy_exists(args.strategy_id)}
    if command == "log-append":
        return append_log(args.strategy_id, payload)
    if command == "log-list":
        return {
            "strategy_id": args.strategy_id,
            "logs": list_logs(
                args.strategy_id,
                limit=args.limit,
                from_ts=args.from_ts,
                to_ts=args.to_ts,
            ),
        }
    if command == "log-show":
        return {
            "strategy_id": args.strategy_id,
            "log": show_log(args.strategy_id, log_id=args.log_id),
        }
    if command == "log-tail":
        return {
            "strategy_id": args.strategy_id,
            "logs": tail_logs(args.strategy_id, limit=args.limit),
        }
    if command == "install-skill":
        return install_skill(
            args.runtime,
            skills_dir_override=getattr(args, "skills_dir", None),
            agents_dir_override=getattr(args, "agents_dir", None),
        )

    raise CliValidationError(f"unsupported command: {command}")
