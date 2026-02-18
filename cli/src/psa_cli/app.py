from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any

from psa_core.contracts import ContractError

from psa_cli.errors import CliError, ExitCode
from psa_cli.handlers import execute_command
from psa_cli.io_json import read_json_input, write_json_output
from psa_cli.parser import build_parser
from psa_cli.schema import validate_request


def _print_error(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def run_command(command: str, *, input_path: str, output_path: str, pretty: bool) -> int:
    payload = read_json_input(input_path)
    validate_request(command, payload)
    response: dict[str, Any] = execute_command(command, payload)
    write_json_output(response, output_path, pretty=pretty)
    return int(ExitCode.OK)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return int(ExitCode.INTERNAL)

    if args.command is None:
        parser.print_help()
        return int(ExitCode.OK)

    try:
        return run_command(
            args.command,
            input_path=args.input_path,
            output_path=args.output_path,
            pretty=args.pretty,
        )
    except CliError as exc:
        _print_error(exc.message)
        return int(exc.exit_code)
    except (ContractError, ValueError) as exc:
        _print_error(str(exc))
        return int(ExitCode.VALIDATION)
    except Exception as exc:  # pragma: no cover - fallback guard
        _print_error(f"unexpected error: {exc}")
        return int(ExitCode.INTERNAL)
