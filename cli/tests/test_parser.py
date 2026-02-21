from __future__ import annotations

import pytest
from psa_cli.errors import CliArgumentsError
from psa_cli.parser import build_parser


def test_parser_parses_upsert_strategy_state() -> None:
    parser = build_parser()
    args = parser.parse_args(["upsert", "strategy-state", "--json", "{}"])
    assert args.group == "upsert"
    assert args.upsert_command == "strategy-state"
    assert args.json == "{}"


def test_parser_parses_evaluate_point_latest_strategy_mode() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "evaluate",
            "point",
            "--strategy-id",
            "strategy-1",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
        ]
    )
    assert args.group == "evaluate"
    assert args.evaluate_command == "point"
    assert args.strategy_id == "strategy-1"
    assert args.version_id is None


def test_parser_raises_argument_error() -> None:
    parser = build_parser()
    with pytest.raises(CliArgumentsError):
        parser.parse_args(["evaluate", "point", "--price", "42"])
