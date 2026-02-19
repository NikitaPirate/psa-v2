from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version

COMMAND_HELP: dict[str, str] = {
    "evaluate-point": "Evaluate one observation point",
    "evaluate-rows": "Evaluate an array of observation rows",
    "evaluate-ranges": "Build rows from ranges and evaluate them",
}


def _cli_version() -> str:
    try:
        return version("psa-cli")
    except PackageNotFoundError:
        return "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="psa")
    parser.add_argument(
        "--version",
        action="version",
        version=f"psa-cli {_cli_version()}",
    )

    subparsers = parser.add_subparsers(dest="command")
    for command, help_text in COMMAND_HELP.items():
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.add_argument(
            "--input",
            dest="input_path",
            required=True,
            help="Input JSON file or -",
        )
        subparser.add_argument(
            "--output",
            dest="output_path",
            required=True,
            help="Output JSON file or -",
        )
        subparser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty-print JSON output",
        )

    return parser
