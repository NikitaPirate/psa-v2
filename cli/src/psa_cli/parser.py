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
        return "0.2.0"


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected boolean value")


def _add_inline_strategy_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version-id")
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

    create_parser = groups.add_parser("create", help="Create entities")
    create_sub = create_parser.add_subparsers(dest="create_command", required=True)

    create_thesis = create_sub.add_parser("thesis", help="Create thesis")
    create_thesis.add_argument("--json")
    create_thesis.add_argument("--id")
    create_thesis.add_argument("--title")
    create_thesis.add_argument("--summary")
    create_thesis.add_argument("--assumption", action="append", default=None)
    create_thesis.add_argument("--invalidation-signal", action="append", default=None)
    create_thesis.add_argument("--horizon")
    create_thesis.add_argument("--status", default="active")

    create_strategy = create_sub.add_parser("strategy", help="Create strategy")
    create_strategy.add_argument("--json")
    create_strategy.add_argument("--id")
    create_strategy.add_argument("--name")
    create_strategy.add_argument("--objective")
    create_strategy.add_argument("--market-mode", choices=["bear", "bull"])
    create_strategy.add_argument("--notes")
    create_strategy.add_argument("--status", default="active")

    create_version = create_sub.add_parser("version", help="Create strategy version")
    create_version.add_argument("--json")
    create_version.add_argument("--id")
    create_version.add_argument("--strategy-id")
    create_version.add_argument("--label")
    create_version.add_argument("--rationale")
    create_version.add_argument("--created-by", default="agent")
    create_version.add_argument("--tag", action="append", default=None)
    create_version.add_argument("--market-mode", choices=["bear", "bull"])
    create_version.add_argument(
        "--price-segment",
        dest="price_segments",
        action="append",
        type=parse_price_segment,
        default=[],
    )
    create_version.add_argument(
        "--time-segment",
        dest="time_segments",
        action="append",
        type=parse_time_segment,
        default=[],
    )

    create_link = create_sub.add_parser("link", help="Link strategy to thesis")
    create_link.add_argument("--strategy-id", required=True)
    create_link.add_argument("--thesis-id", required=True)
    create_link.add_argument("--rationale", default="")

    create_checkin = create_sub.add_parser("checkin", help="Create checkin")
    create_checkin.add_argument("--id")
    create_checkin.add_argument("--strategy-id", required=True)
    create_checkin.add_argument("--timestamp")
    create_checkin.add_argument("--price", type=float)
    create_checkin.add_argument("--context")
    create_checkin.add_argument("--evaluation-json")
    create_checkin.add_argument("--note")

    create_decision = create_sub.add_parser("decision", help="Create decision")
    create_decision.add_argument("--id")
    create_decision.add_argument("--strategy-id", required=True)
    create_decision.add_argument("--timestamp")
    create_decision.add_argument("--action-summary", required=True)
    create_decision.add_argument("--rationale")
    create_decision.add_argument("--linked-checkin-id")

    create_pack = create_sub.add_parser("strategy-pack", help="Atomic first-save pack")
    create_pack.add_argument("--json", required=True)

    update_parser = groups.add_parser("update", help="Update entities")
    update_sub = update_parser.add_subparsers(dest="update_command", required=True)

    update_thesis = update_sub.add_parser("thesis", help="Update thesis")
    update_thesis.add_argument("--id", required=True)
    update_thesis.add_argument("--title")
    update_thesis.add_argument("--summary")
    update_thesis.add_argument("--assumption", action="append", default=None)
    update_thesis.add_argument("--invalidation-signal", action="append", default=None)
    update_thesis.add_argument("--horizon")
    update_thesis.add_argument("--status")

    update_strategy = update_sub.add_parser("strategy", help="Update strategy")
    update_strategy.add_argument("--id", required=True)
    update_strategy.add_argument("--name")
    update_strategy.add_argument("--objective")
    update_strategy.add_argument("--market-mode", choices=["bear", "bull"])
    update_strategy.add_argument("--notes")
    update_strategy.add_argument("--status")
    update_strategy.add_argument("--set-active", action="store_true")

    update_profile = update_sub.add_parser("profile", help="Update user profile")
    update_profile.add_argument("--user-id")
    update_profile.add_argument("--language")
    update_profile.add_argument("--philosophy")
    update_profile.add_argument("--constraint", action="append", default=None)
    update_profile.add_argument("--active-strategy-id")
    update_profile.add_argument("--runtime-mode", choices=["auto", "tool"])
    update_profile.add_argument("--runtime-package")
    update_profile.add_argument("--runtime-command")
    update_profile.add_argument("--runtime-resolved", type=_parse_bool)

    update_pack = update_sub.add_parser("strategy-pack", help="Atomic revision-save pack")
    update_pack.add_argument("--json", required=True)

    evaluate_parser = groups.add_parser("evaluate", help="Evaluate strategies")
    evaluate_sub = evaluate_parser.add_subparsers(dest="evaluate_command", required=True)

    eval_point = evaluate_sub.add_parser("point", help="Evaluate point")
    _add_inline_strategy_flags(eval_point)
    eval_point.add_argument("--timestamp", required=True)
    eval_point.add_argument("--price", required=True, type=float)

    eval_rows = evaluate_sub.add_parser("rows", help="Evaluate rows")
    _add_inline_strategy_flags(eval_rows)
    eval_rows.add_argument("--row", dest="rows", action="append", type=parse_row, default=[])

    eval_ranges = evaluate_sub.add_parser("ranges", help="Evaluate generated ranges")
    _add_inline_strategy_flags(eval_ranges)
    eval_ranges.add_argument("--price-start", required=True, type=float)
    eval_ranges.add_argument("--price-end", required=True, type=float)
    eval_ranges.add_argument("--price-steps", required=True, type=int)
    eval_ranges.add_argument("--time-start", required=True)
    eval_ranges.add_argument("--time-end", required=True)
    eval_ranges.add_argument("--time-steps", required=True, type=int)
    eval_ranges.add_argument("--include-price-breakpoints", action="store_true")

    return parser
