from __future__ import annotations

from typing import Any

from psa_cli.arg_types import parse_json_string
from psa_cli.commands_create import apply_strategy_pack
from psa_cli.errors import CliStateError
from psa_cli.store import MemoryStore


def _compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def execute_update(args: Any, store: MemoryStore) -> dict[str, Any]:
    if args.update_command == "thesis":
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
        tx = store.apply({"op": "upsert_thesis", "thesis": payload}, create_if_missing=False)
        return {"command": "update thesis", **tx}

    if args.update_command == "strategy":
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

        operations = [{"op": "upsert_strategy", "strategy": payload}]
        if args.set_active:
            operations.append({"op": "set_active_strategy", "strategy_id": args.id})

        tx = store.apply_batch(operations, create_if_missing=False)
        return {"command": "update strategy", **tx}

    if args.update_command == "profile":
        runtime: dict[str, Any] | None = None
        if any(
            value is not None
            for value in (
                args.runtime_mode,
                args.runtime_package,
                args.runtime_command,
                args.runtime_resolved,
            )
        ):
            runtime = _compact_dict(
                {
                    "mode": args.runtime_mode,
                    "package_name": args.runtime_package,
                    "command": args.runtime_command,
                    "resolved": args.runtime_resolved,
                }
            )

        payload = _compact_dict(
            {
                "user_id": args.user_id,
                "language": args.language,
                "philosophy": args.philosophy,
                "constraints": args.constraint if args.constraint is not None else None,
                "active_strategy_id": args.active_strategy_id,
                "cli_runtime": runtime,
            }
        )
        tx = store.apply({"op": "upsert_profile", "profile": payload}, create_if_missing=True)
        return {"command": "update profile", **tx}

    if args.update_command == "strategy-pack":
        payload = parse_json_string(args.json, field_name="--json")
        tx = apply_strategy_pack(store, payload, mode="update")
        return {"command": "update strategy-pack", **tx}

    raise CliStateError(
        f"unsupported update command: {args.update_command}",
        error_code="unsupported_command",
    )
