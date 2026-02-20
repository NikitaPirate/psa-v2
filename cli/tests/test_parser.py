from __future__ import annotations

import pytest
from psa_cli.errors import CliArgumentsError
from psa_cli.parser import build_parser


def test_parser_parses_show_strategy_with_includes() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "show",
            "strategy",
            "--id",
            "strategy-1",
            "--include",
            "versions",
            "--include",
            "theses",
        ]
    )
    assert args.group == "show"
    assert args.show_command == "strategy"
    assert args.id == "strategy-1"
    assert args.include == ["versions", "theses"]


def test_parser_parses_evaluate_point_inline() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "evaluate",
            "point",
            "--market-mode",
            "bear",
            "--price-segment",
            "50000:60000:10",
            "--price-segment",
            "40000:50000:20",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
        ]
    )
    assert args.group == "evaluate"
    assert args.evaluate_command == "point"
    assert args.market_mode == "bear"
    assert len(args.price_segments) == 2
    assert args.price == 42000


def test_parser_raises_argument_error() -> None:
    parser = build_parser()
    with pytest.raises(CliArgumentsError):
        parser.parse_args(["evaluate", "point", "--price", "42"])
