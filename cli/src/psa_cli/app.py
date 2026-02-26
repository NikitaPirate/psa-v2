from __future__ import annotations

import json
import sys
from argparse import Namespace
from collections.abc import Sequence
from typing import Any

from psa_core.contracts import ContractError

from psa_cli.errors import CliArgumentError, CliError, ExitCode
from psa_cli.handlers import execute_command
from psa_cli.io_json import read_json_input, write_json_output
from psa_cli.parser import build_parser
from psa_cli.schema import validate_request

INPUT_COMMANDS = {
    "evaluate-point",
    "evaluate-portfolio",
    "evaluate-rows",
    "evaluate-ranges",
    "strategy-upsert",
    "log-append",
}


def _print_error(*, error_code: str, message: str, details: Any = None) -> None:
    payload = {"error": {"code": error_code, "message": message, "details": details}}
    sys.stderr.write(json.dumps(payload, separators=(",", ":"), sort_keys=False) + "\n")


def run_command(args: Namespace) -> int:
    if not getattr(args, "json_output", False):
        raise CliArgumentError("--json is required")

    payload: Any = None
    if args.command_key in INPUT_COMMANDS:
        payload = read_json_input(args.input_path)
        validate_request(args.command_key, payload)

    response = execute_command(args.command_key, payload, args=args)
    output_path = getattr(args, "output_path", "-")
    pretty = bool(getattr(args, "pretty", False))
    write_json_output(response, output_path, pretty=pretty)
    return int(ExitCode.OK)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except CliArgumentError as exc:
        _print_error(error_code=exc.error_code, message=exc.message, details=exc.details)
        return int(exc.exit_code)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return int(ExitCode.INTERNAL)

    if args.command_key is None:
        parser.print_help()
        return int(ExitCode.OK)

    try:
        return run_command(args)
    except CliError as exc:
        _print_error(error_code=exc.error_code, message=exc.message, details=exc.details)
        return int(exc.exit_code)
    except (ContractError, ValueError) as exc:
        _print_error(error_code="validation_error", message=str(exc), details=None)
        return int(ExitCode.VALIDATION)
    except Exception as exc:  # pragma: no cover - fallback guard
        _print_error(error_code="internal_error", message="unexpected error", details=str(exc))
        return int(ExitCode.INTERNAL)
