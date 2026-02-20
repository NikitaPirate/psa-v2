from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from psa_core.contracts import ContractError

from psa_cli.errors import (
    CliArgumentsError,
    CliError,
    CliInternalError,
    CliRuntimeError,
    CliStateError,
    CliValidationError,
    ExitCode,
)
from psa_cli.handlers import execute
from psa_cli.output import render_error, render_success
from psa_cli.parser import build_parser
from psa_cli.store import MemoryStore, StoreError, store_error_code


def _print_error(error_payload: str) -> None:
    sys.stderr.write(error_payload)


def _print_success(payload: str) -> None:
    sys.stdout.write(payload)


def _store_error_to_cli_error(exc: StoreError) -> CliError:
    code = store_error_code(exc)
    message = str(exc)

    if code in {"invalid_store_json", "invalid_store_shape"}:
        return CliRuntimeError(message, error_code=code)

    if (
        code.endswith("_not_found")
        or code.endswith("_missing")
        or code.startswith("strategy_") and code.endswith("_missing")
    ):
        return CliStateError(message, error_code=code)

    if "conflict" in code:
        return CliStateError(message, error_code=code)

    if code.startswith("store_"):
        return CliStateError(message, error_code=code)

    return CliValidationError(message, error_code=code)


def _emit_cli_error(exc: CliError, *, pretty: bool) -> int:
    _print_error(
        render_error(
            code=exc.error_code,
            message=exc.message,
            pretty=pretty,
        )
    )
    return int(exc.exit_code)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()

    args = None
    try:
        args = parser.parse_args(argv)
    except CliArgumentsError as exc:
        return _emit_cli_error(exc, pretty=False)
    except SystemExit as exc:  # pragma: no cover - argparse version/help exits
        if isinstance(exc.code, int):
            return exc.code
        return int(ExitCode.INTERNAL)

    pretty = bool(args.pretty)

    try:
        db_path = Path(args.db_path).resolve() if args.db_path else None
        store = MemoryStore(path=db_path)
        result = execute(args, store)
        _print_success(render_success(result, output_format=args.output_format, pretty=pretty))
        return int(ExitCode.OK)
    except CliError as exc:
        return _emit_cli_error(exc, pretty=pretty)
    except StoreError as exc:
        return _emit_cli_error(_store_error_to_cli_error(exc), pretty=pretty)
    except (ContractError, ValueError) as exc:
        return _emit_cli_error(
            CliValidationError(str(exc), error_code="validation_error"),
            pretty=pretty,
        )
    except OSError as exc:
        return _emit_cli_error(
            CliRuntimeError(str(exc), error_code="runtime_error"),
            pretty=pretty,
        )
    except Exception as exc:  # pragma: no cover - fallback guard
        return _emit_cli_error(
            CliInternalError(f"unexpected error: {exc}", error_code="internal_error"),
            pretty=pretty,
        )
