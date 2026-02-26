from __future__ import annotations

import pytest
from psa_cli.errors import CliArgumentError
from psa_cli.parser import build_parser
from psa_cli.skills import supported_runtimes


def test_parser_parses_strategy_upsert() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "strategy",
            "upsert",
            "--strategy-id",
            "main",
            "--input",
            "strategy.json",
            "--json",
        ]
    )
    assert args.command_key == "strategy-upsert"
    assert args.strategy_id == "main"
    assert args.input_path == "strategy.json"
    assert args.json_output is True


def test_parser_parses_evaluate_point_with_strategy_id() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "evaluate-point",
            "--strategy-id",
            "main",
            "--input",
            "request.json",
            "--output",
            "-",
            "--json",
            "--pretty",
        ]
    )
    assert args.command_key == "evaluate-point"
    assert args.strategy_id == "main"
    assert args.pretty is True


def test_parser_parses_evaluate_portfolio_with_strategy_id() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "evaluate-portfolio",
            "--strategy-id",
            "main",
            "--input",
            "request.json",
            "--output",
            "-",
            "--json",
        ]
    )
    assert args.command_key == "evaluate-portfolio"
    assert args.strategy_id == "main"
    assert args.json_output is True


def test_parser_requires_json_flag() -> None:
    parser = build_parser()
    with pytest.raises(CliArgumentError):
        parser.parse_args(
            ["strategy", "list"],
        )


def test_parser_parses_install_skill_with_supported_runtime() -> None:
    parser = build_parser()
    args = parser.parse_args(["install-skill", "codex", "--json"])
    assert args.command_key == "install-skill"
    assert args.runtime == "codex"
    assert args.skills_dir is None
    assert args.agents_dir is None
    assert args.json_output is True


def test_parser_parses_install_skill_with_custom_dirs() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "install-skill",
            "openclaw",
            "--skills-dir",
            "/tmp/skills",
            "--agents-dir",
            "/tmp/agents",
            "--json",
        ]
    )
    assert args.command_key == "install-skill"
    assert args.runtime == "openclaw"
    assert args.skills_dir == "/tmp/skills"
    assert args.agents_dir == "/tmp/agents"
    assert args.json_output is True


@pytest.mark.parametrize("runtime", supported_runtimes())
def test_parser_install_skill_runtime_choices_match_runtime_config(runtime: str) -> None:
    parser = build_parser()
    args = parser.parse_args(["install-skill", runtime, "--json"])
    assert args.runtime == runtime
