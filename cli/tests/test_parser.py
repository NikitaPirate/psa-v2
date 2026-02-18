from __future__ import annotations

from psa_cli.parser import build_parser


def test_parser_parses_evaluate_point_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["evaluate-point", "--input", "request.json", "--output", "-", "--pretty"]
    )
    assert args.command == "evaluate-point"
    assert args.input_path == "request.json"
    assert args.output_path == "-"
    assert args.pretty is True


def test_parser_allows_help_without_command() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command is None
