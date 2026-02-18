from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import FormatChecker, validate

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
EXAMPLES = ROOT / "examples"
FORMAT_CHECKER = FormatChecker()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_cli(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PSA_SCHEMA_DIR"] = str(SCHEMAS)
    pythonpath_parts = [str(ROOT / "cli" / "src"), str(ROOT / "core" / "src")]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return subprocess.run(
        [sys.executable, "-m", "psa_cli", *args],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


def test_evaluate_commands_return_schema_valid_responses() -> None:
    cases = [
        (
            "evaluate-point",
            EXAMPLES / "bear_accumulate_point.json",
            SCHEMAS / "evaluate_point.response.v1.json",
        ),
        (
            "evaluate-rows",
            EXAMPLES / "batch_timeseries_rows.json",
            SCHEMAS / "evaluate_rows.response.v1.json",
        ),
        (
            "evaluate-ranges",
            EXAMPLES / "range_timeseries_rows.json",
            SCHEMAS / "evaluate_rows.response.v1.json",
        ),
    ]

    for command, request_path, response_schema_path in cases:
        completed = _run_cli([command, "--input", str(request_path), "--output", "-"])
        assert completed.returncode == 0, completed.stderr
        response = json.loads(completed.stdout)
        validate(
            instance=response,
            schema=_load_json(response_schema_path),
            format_checker=FORMAT_CHECKER,
        )


def test_evaluate_point_supports_stdin_stdout() -> None:
    request_payload = (EXAMPLES / "bear_accumulate_point.json").read_text(encoding="utf-8")
    completed = _run_cli(
        ["evaluate-point", "--input", "-", "--output", "-", "--pretty"],
        input_text=request_payload,
    )
    assert completed.returncode == 0, completed.stderr
    response = json.loads(completed.stdout)
    assert "row" in response
    assert completed.stdout.endswith("\n")
    assert "\n  " in completed.stdout


def test_cli_returns_code_2_on_invalid_arguments() -> None:
    completed = _run_cli(["evaluate-point"])
    assert completed.returncode == 2


def test_cli_returns_code_3_on_missing_input_file() -> None:
    completed = _run_cli(["evaluate-point", "--input", "missing.json", "--output", "-"])
    assert completed.returncode == 3
    assert "failed to read input" in completed.stderr


def test_cli_returns_code_3_on_invalid_json() -> None:
    completed = _run_cli(
        ["evaluate-point", "--input", "-", "--output", "-"],
        input_text="{",
    )
    assert completed.returncode == 3
    assert "invalid JSON" in completed.stderr


def test_cli_returns_code_4_on_schema_violation(tmp_path: Path) -> None:
    payload = _load_json(EXAMPLES / "bear_accumulate_point.json")
    payload["strategy"]["market_mode"] = "sideways"

    path = tmp_path / "bad_request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    completed = _run_cli(["evaluate-point", "--input", str(path), "--output", "-"])
    assert completed.returncode == 4
    assert "request does not match schema" in completed.stderr


def test_cli_returns_code_4_on_runtime_validation_error(tmp_path: Path) -> None:
    payload = _load_json(EXAMPLES / "bear_accumulate_point.json")
    payload["strategy"]["price_segments"] = [
        {"price_low": 40_000, "price_high": 50_000, "weight": 50},
        {"price_low": 49_000, "price_high": 60_000, "weight": 50},
    ]

    path = tmp_path / "overlap_request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    completed = _run_cli(["evaluate-point", "--input", str(path), "--output", "-"])
    assert completed.returncode == 4
    assert "overlap" in completed.stderr
