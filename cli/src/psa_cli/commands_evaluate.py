from __future__ import annotations

from typing import Any

from psa_core.contracts import (
    evaluate_point_payload,
    evaluate_rows_from_ranges_payload,
    evaluate_rows_payload,
)

from psa_cli.arg_types import ensure_datetime
from psa_cli.errors import CliValidationError
from psa_cli.store import MemoryStore


def _has_inline_spec(args: Any) -> bool:
    return bool(args.market_mode is not None or args.price_segments or args.time_segments)


def _inline_strategy_spec(args: Any) -> dict[str, Any]:
    if args.market_mode is None:
        raise CliValidationError(
            "market-mode is required for inline strategy",
            error_code="missing_market_mode",
        )
    if not args.price_segments:
        raise CliValidationError(
            "at least one --price-segment is required for inline strategy",
            error_code="missing_price_segments",
        )
    return {
        "market_mode": args.market_mode,
        "price_segments": args.price_segments,
        "time_segments": args.time_segments or [],
    }


def _resolve_strategy_spec(args: Any, store: MemoryStore) -> tuple[dict[str, Any], str]:
    inline_spec = _has_inline_spec(args)

    if args.version_id and inline_spec:
        raise CliValidationError(
            "cannot combine --version-id with inline strategy flags",
            error_code="conflicting_strategy_source",
        )

    if args.version_id and args.strategy_id:
        raise CliValidationError(
            "cannot combine --version-id with --strategy-id",
            error_code="conflicting_strategy_source",
        )

    if args.version_id:
        spec = store.get_strategy_spec_by_version(args.version_id)
        return spec, f"version:{args.version_id}"

    if inline_spec:
        return _inline_strategy_spec(args), "inline"

    spec, strategy_id, version_id = store.get_latest_strategy_spec(strategy_id=args.strategy_id)
    return spec, f"latest:{strategy_id}:{version_id}"


def execute_evaluate(args: Any, store: MemoryStore) -> dict[str, Any]:
    strategy_spec, source = _resolve_strategy_spec(args, store)

    if args.evaluate_command == "point":
        payload = {
            "strategy": strategy_spec,
            "timestamp": ensure_datetime(args.timestamp, field_name="timestamp"),
            "price": args.price,
        }
        response = evaluate_point_payload(payload)
        return {
            "command": "evaluate point",
            "strategy_source": source,
            "data": response,
        }

    if args.evaluate_command == "rows":
        if not args.rows:
            raise CliValidationError(
                "at least one --row is required",
                error_code="missing_rows",
            )
        payload = {
            "strategy": strategy_spec,
            "rows": args.rows,
        }
        response = evaluate_rows_payload(payload)
        return {
            "command": "evaluate rows",
            "strategy_source": source,
            "data": response,
        }

    if args.evaluate_command == "ranges":
        payload = {
            "strategy": strategy_spec,
            "price_start": args.price_start,
            "price_end": args.price_end,
            "price_steps": args.price_steps,
            "time_start": ensure_datetime(args.time_start, field_name="time_start"),
            "time_end": ensure_datetime(args.time_end, field_name="time_end"),
            "time_steps": args.time_steps,
            "include_price_breakpoints": args.include_price_breakpoints,
        }
        response = evaluate_rows_from_ranges_payload(payload)
        return {
            "command": "evaluate ranges",
            "strategy_source": source,
            "data": response,
        }

    raise CliValidationError(
        f"unsupported evaluate command: {args.evaluate_command}",
        error_code="unsupported_command",
    )
