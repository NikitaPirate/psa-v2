from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

from psa_cli.errors import CliStateError
from psa_cli.store import MemoryStore


def _cli_version() -> str:
    try:
        return version("psa-strategy-cli")
    except PackageNotFoundError:
        return "0.3.0"


def execute_show(args: Any, store: MemoryStore) -> dict[str, Any]:
    if args.show_command == "runtime":
        return {
            "command": "show runtime",
            "runtime": {
                "command": "psa",
                "package": "psa-strategy-cli",
                "version": _cli_version(),
                "db_path": str(store.path),
            },
        }

    if args.show_command == "memory":
        data = store.read(view=args.view, create_if_missing=True)
        return {
            "command": "show memory",
            "view": args.view,
            "memory": data,
        }

    if args.show_command == "strategy":
        full = store.get_full_store(create_if_missing=True)
        strategy = full.get("strategies", {}).get(args.id)
        if not isinstance(strategy, dict):
            raise CliStateError(f"strategy not found: {args.id}", error_code="strategy_not_found")

        include = set(args.include or [])
        payload: dict[str, Any] = {
            "id": args.id,
            "strategy": strategy,
        }

        if "versions" in include:
            versions: list[dict[str, Any]] = []
            for item in full.get("strategy_versions", {}).values():
                if isinstance(item, dict) and item.get("strategy_id") == args.id:
                    versions.append(item)
            payload["versions"] = sorted(versions, key=lambda x: str(x.get("created_at", "")))

        if "theses" in include:
            thesis_ids = [
                link.get("thesis_id")
                for link in full.get("strategy_thesis_links", [])
                if isinstance(link, dict) and link.get("strategy_id") == args.id
            ]
            theses: list[dict[str, Any]] = []
            for thesis_id in thesis_ids:
                thesis = full.get("theses", {}).get(thesis_id)
                if isinstance(thesis, dict):
                    theses.append(thesis)
            payload["theses"] = theses

        if "checkins" in include:
            checkins = [
                item
                for item in full.get("checkins", [])
                if isinstance(item, dict) and item.get("strategy_id") == args.id
            ]
            payload["checkins"] = sorted(checkins, key=lambda x: str(x.get("timestamp", "")))

        if "decisions" in include:
            decisions = [
                item
                for item in full.get("decision_log", [])
                if isinstance(item, dict) and item.get("strategy_id") == args.id
            ]
            payload["decisions"] = sorted(decisions, key=lambda x: str(x.get("timestamp", "")))

        return {
            "command": "show strategy",
            "data": payload,
        }

    if args.show_command == "thesis":
        full = store.get_full_store(create_if_missing=True)
        thesis = full.get("theses", {}).get(args.id)
        if not isinstance(thesis, dict):
            raise CliStateError(f"thesis not found: {args.id}", error_code="thesis_not_found")
        return {
            "command": "show thesis",
            "id": args.id,
            "thesis": thesis,
        }

    if args.show_command == "checkins":
        full = store.get_full_store(create_if_missing=True)
        if args.strategy_id not in full.get("strategies", {}):
            raise CliStateError(
                f"strategy not found: {args.strategy_id}",
                error_code="strategy_not_found",
            )
        checkins = [
            item
            for item in full.get("checkins", [])
            if isinstance(item, dict) and item.get("strategy_id") == args.strategy_id
        ]
        checkins = sorted(checkins, key=lambda x: str(x.get("timestamp", "")), reverse=True)
        return {
            "command": "show checkins",
            "strategy_id": args.strategy_id,
            "count": len(checkins),
            "checkins": checkins[: args.limit],
        }

    if args.show_command == "decisions":
        full = store.get_full_store(create_if_missing=True)
        if args.strategy_id not in full.get("strategies", {}):
            raise CliStateError(
                f"strategy not found: {args.strategy_id}",
                error_code="strategy_not_found",
            )
        decisions = [
            item
            for item in full.get("decision_log", [])
            if isinstance(item, dict) and item.get("strategy_id") == args.strategy_id
        ]
        decisions = sorted(decisions, key=lambda x: str(x.get("timestamp", "")), reverse=True)
        return {
            "command": "show decisions",
            "strategy_id": args.strategy_id,
            "count": len(decisions),
            "decisions": decisions[: args.limit],
        }

    raise CliStateError(
        f"unsupported show command: {args.show_command}",
        error_code="unsupported_command",
    )
