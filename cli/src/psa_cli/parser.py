from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version
from typing import Any, NoReturn

from psa_cli.errors import CliArgumentError


class CliArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CliArgumentError(message)


def _cli_version() -> str:
    try:
        return version("psa-strategy-cli")
    except PackageNotFoundError:
        return "0.1.0"


def _add_required_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        required=True,
        help="Require JSON mode for machine consumption",
    )


def _add_evaluate_commands(subparsers: Any) -> None:
    evaluate_help = {
        "evaluate-point": "Evaluate one observation point",
        "evaluate-rows": "Evaluate an array of observation rows",
        "evaluate-ranges": "Build rows from ranges and evaluate them",
    }
    for command, help_text in evaluate_help.items():
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.set_defaults(command_key=command)
        subparser.add_argument("--strategy-id", required=True, help="Stored strategy id")
        subparser.add_argument(
            "--input", dest="input_path", required=True, help="Input JSON file or -"
        )
        subparser.add_argument(
            "--output", dest="output_path", required=True, help="Output JSON file or -"
        )
        _add_required_json_flag(subparser)
        subparser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")


def _add_strategy_commands(subparsers: Any) -> None:
    strategy_parser = subparsers.add_parser("strategy", help="Strategy storage operations")
    strategy_subparsers = strategy_parser.add_subparsers(dest="strategy_command", required=True)

    upsert = strategy_subparsers.add_parser("upsert", help="Create or update a strategy")
    upsert.set_defaults(command_key="strategy-upsert")
    upsert.add_argument("--strategy-id", required=True, help="Strategy id")
    upsert.add_argument("--input", dest="input_path", required=True, help="Input JSON file or -")
    _add_required_json_flag(upsert)

    list_cmd = strategy_subparsers.add_parser("list", help="List stored strategies")
    list_cmd.set_defaults(command_key="strategy-list")
    _add_required_json_flag(list_cmd)

    show = strategy_subparsers.add_parser("show", help="Show one stored strategy")
    show.set_defaults(command_key="strategy-show")
    show.add_argument("--strategy-id", required=True, help="Strategy id")
    _add_required_json_flag(show)

    exists = strategy_subparsers.add_parser("exists", help="Check strategy existence")
    exists.set_defaults(command_key="strategy-exists")
    exists.add_argument("--strategy-id", required=True, help="Strategy id")
    _add_required_json_flag(exists)


def _add_log_commands(subparsers: Any) -> None:
    log_parser = subparsers.add_parser("log", help="Log storage operations")
    log_subparsers = log_parser.add_subparsers(dest="log_command", required=True)

    append = log_subparsers.add_parser("append", help="Append one log record")
    append.set_defaults(command_key="log-append")
    append.add_argument("--strategy-id", required=True, help="Strategy id")
    append.add_argument("--input", dest="input_path", required=True, help="Input JSON file or -")
    _add_required_json_flag(append)

    list_cmd = log_subparsers.add_parser("list", help="List log records")
    list_cmd.set_defaults(command_key="log-list")
    list_cmd.add_argument("--strategy-id", required=True, help="Strategy id")
    list_cmd.add_argument("--limit", type=int, required=False, default=None, help="Maximum items")
    list_cmd.add_argument("--from-ts", required=False, default=None, help="Lower RFC3339 bound")
    list_cmd.add_argument("--to-ts", required=False, default=None, help="Upper RFC3339 bound")
    _add_required_json_flag(list_cmd)

    show = log_subparsers.add_parser("show", help="Show one log record by id")
    show.set_defaults(command_key="log-show")
    show.add_argument("--strategy-id", required=True, help="Strategy id")
    show.add_argument("--log-id", required=True, help="Log id")
    _add_required_json_flag(show)

    tail = log_subparsers.add_parser("tail", help="Return last N log records")
    tail.set_defaults(command_key="log-tail")
    tail.add_argument("--strategy-id", required=True, help="Strategy id")
    tail.add_argument("--limit", type=int, required=True, help="Tail size")
    _add_required_json_flag(tail)


def build_parser() -> argparse.ArgumentParser:
    parser = CliArgumentParser(prog="psa")
    parser.add_argument("--version", action="version", version=f"psa-strategy-cli {_cli_version()}")

    subparsers = parser.add_subparsers(dest="command_key")
    _add_evaluate_commands(subparsers)
    _add_strategy_commands(subparsers)
    _add_log_commands(subparsers)
    return parser
