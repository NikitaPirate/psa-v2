from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version

from psa_cli.arg_types import parse_price_segment, parse_row, parse_time_segment
from psa_cli.errors import CliArgumentsError


class _CliArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # pragma: no cover - argparse hook
        raise CliArgumentsError(message, error_code="arguments_error")


def _cli_version() -> str:
    try:
        return version("psa-strategy-cli")
    except PackageNotFoundError:
        return "0.3.0"


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected boolean value")


def _add_strategy_source_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version-id")
    parser.add_argument("--strategy-id")
    parser.add_argument("--market-mode", choices=["bear", "bull"])
    parser.add_argument(
        "--price-segment",
        dest="price_segments",
        action="append",
        type=parse_price_segment,
        default=[],
        help="Segment in format low:high:weight",
    )
    parser.add_argument(
        "--time-segment",
        dest="time_segments",
        action="append",
        type=parse_time_segment,
        default=[],
        help="Segment in format start:end:k_start:k_end",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = _CliArgumentParser(prog="psa")
    parser.add_argument(
        "--version",
        action="version",
        version=f"psa-strategy-cli {_cli_version()}",
    )
    parser.add_argument("--format", dest="output_format", choices=["json", "text"], default="json")
    parser.add_argument("--pretty", action="store_true", help="Pretty output for JSON envelopes")
    parser.add_argument("--db-path", default=None, help=argparse.SUPPRESS)

    groups = parser.add_subparsers(dest="group", required=True)

    show_parser = groups.add_parser("show", help="Read runtime and memory state")
    show_sub = show_parser.add_subparsers(dest="show_command", required=True)

    show_sub.add_parser("runtime", help="Show CLI runtime info")

    show_memory = show_sub.add_parser("memory", help="Show memory snapshot")
    show_memory.add_argument("--view", choices=["summary", "full"], default="summary")

    show_strategy = show_sub.add_parser(
        "strategy",
        help="Show strategy and optional linked entities",
    )
    show_strategy.add_argument("--id", required=True)
    show_strategy.add_argument(
        "--include",
        action="append",
        choices=["versions", "theses", "checkins", "decisions"],
        default=[],
    )

    show_thesis = show_sub.add_parser("thesis", help="Show one thesis")
    show_thesis.add_argument("--id", required=True)

    show_checkins = show_sub.add_parser("checkins", help="Show strategy checkins")
    show_checkins.add_argument("--strategy-id", required=True)
    show_checkins.add_argument("--limit", type=int, default=20)

    show_decisions = show_sub.add_parser("decisions", help="Show strategy decisions")
    show_decisions.add_argument("--strategy-id", required=True)
    show_decisions.add_argument("--limit", type=int, default=20)

    upsert_parser = groups.add_parser("upsert", help="Upsert entities")
    upsert_sub = upsert_parser.add_subparsers(dest="upsert_command", required=True)

    upsert_thesis = upsert_sub.add_parser("thesis", help="Upsert thesis")
    upsert_thesis.add_argument("--json")
    upsert_thesis.add_argument("--id")
    upsert_thesis.add_argument("--title")
    upsert_thesis.add_argument("--summary")
    upsert_thesis.add_argument("--assumption", action="append", default=None)
    upsert_thesis.add_argument("--invalidation-signal", action="append", default=None)
    upsert_thesis.add_argument("--horizon")
    upsert_thesis.add_argument("--status", default="active")

    upsert_strategy = upsert_sub.add_parser("strategy", help="Upsert strategy")
    upsert_strategy.add_argument("--json")
    upsert_strategy.add_argument("--id")
    upsert_strategy.add_argument("--name")
    upsert_strategy.add_argument("--objective")
    upsert_strategy.add_argument("--market-mode", choices=["bear", "bull"])
    upsert_strategy.add_argument("--notes")
    upsert_strategy.add_argument("--status", default="active")
    upsert_strategy.add_argument("--set-active", action="store_true")

    upsert_profile = upsert_sub.add_parser("profile", help="Upsert user profile")
    upsert_profile.add_argument("--user-id")
    upsert_profile.add_argument("--language")
    upsert_profile.add_argument("--philosophy")
    upsert_profile.add_argument("--constraint", action="append", default=None)
    upsert_profile.add_argument("--active-strategy-id")
    upsert_profile.add_argument("--runtime-mode", choices=["auto", "tool"])
    upsert_profile.add_argument("--runtime-package")
    upsert_profile.add_argument("--runtime-command")
    upsert_profile.add_argument("--runtime-resolved", type=_parse_bool)

    upsert_version = upsert_sub.add_parser("version", help="Upsert strategy version")
    upsert_version.add_argument("--json")
    upsert_version.add_argument("--id")
    upsert_version.add_argument("--strategy-id")
    upsert_version.add_argument("--label")
    upsert_version.add_argument("--rationale")
    upsert_version.add_argument("--created-by", default="agent")
    upsert_version.add_argument("--tag", action="append", default=None)
    upsert_version.add_argument("--market-mode", choices=["bear", "bull"])
    upsert_version.add_argument(
        "--price-segment",
        dest="price_segments",
        action="append",
        type=parse_price_segment,
        default=[],
    )
    upsert_version.add_argument(
        "--time-segment",
        dest="time_segments",
        action="append",
        type=parse_time_segment,
        default=[],
    )

    upsert_link = upsert_sub.add_parser("link", help="Upsert strategy-thesis link")
    upsert_link.add_argument("--strategy-id", required=True)
    upsert_link.add_argument("--thesis-id", required=True)
    upsert_link.add_argument("--rationale", default="")

    upsert_checkin = upsert_sub.add_parser("checkin", help="Upsert checkin")
    upsert_checkin.add_argument("--id")
    upsert_checkin.add_argument("--strategy-id", required=True)
    upsert_checkin.add_argument("--timestamp")
    upsert_checkin.add_argument("--price", type=float)
    upsert_checkin.add_argument("--context")
    upsert_checkin.add_argument("--evaluation-json")
    upsert_checkin.add_argument("--note")

    upsert_decision = upsert_sub.add_parser("decision", help="Upsert decision")
    upsert_decision.add_argument("--id")
    upsert_decision.add_argument("--strategy-id", required=True)
    upsert_decision.add_argument("--timestamp")
    upsert_decision.add_argument("--action-summary", required=True)
    upsert_decision.add_argument("--rationale")
    upsert_decision.add_argument("--linked-checkin-id")

    upsert_state = upsert_sub.add_parser(
        "strategy-state",
        help="Atomic strategy save payload",
    )
    upsert_state.add_argument("--json", required=True)

    evaluate_parser = groups.add_parser("evaluate", help="Evaluate strategies")
    evaluate_sub = evaluate_parser.add_subparsers(dest="evaluate_command", required=True)

    eval_point = evaluate_sub.add_parser("point", help="Evaluate point")
    _add_strategy_source_flags(eval_point)
    eval_point.add_argument("--timestamp", required=True)
    eval_point.add_argument("--price", required=True, type=float)

    eval_rows = evaluate_sub.add_parser("rows", help="Evaluate rows")
    _add_strategy_source_flags(eval_rows)
    eval_rows.add_argument("--row", dest="rows", action="append", type=parse_row, default=[])

    eval_ranges = evaluate_sub.add_parser("ranges", help="Evaluate generated ranges")
    _add_strategy_source_flags(eval_ranges)
    eval_ranges.add_argument("--price-start", required=True, type=float)
    eval_ranges.add_argument("--price-end", required=True, type=float)
    eval_ranges.add_argument("--price-steps", required=True, type=int)
    eval_ranges.add_argument("--time-start", required=True)
    eval_ranges.add_argument("--time-end", required=True)
    eval_ranges.add_argument("--time-steps", required=True, type=int)
    eval_ranges.add_argument("--include-price-breakpoints", action="store_true")

    return parser
