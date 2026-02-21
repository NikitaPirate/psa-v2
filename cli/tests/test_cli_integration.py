from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from jsonschema import FormatChecker, validate

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
FORMAT_CHECKER = FormatChecker()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _strategy_payload() -> dict:
    return {
        "market_mode": "bear",
        "price_segments": [{"price_low": 40_000, "price_high": 50_000, "weight": 100}],
        "time_segments": [],
    }


def _run_cli(
    args: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
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
        cwd=cwd,
        env=env,
        check=False,
    )


def _assert_error_payload(stderr_text: str, *, code: str) -> None:
    payload = json.loads(stderr_text)
    assert payload["error"]["code"] == code
    assert isinstance(payload["error"]["message"], str)
    assert "details" in payload["error"]


def test_strategy_upsert_and_show(tmp_path: Path) -> None:
    upsert = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert upsert.returncode == 0, upsert.stderr
    upsert_payload = json.loads(upsert.stdout)
    assert upsert_payload["strategy_id"] == "main"
    assert upsert_payload["result"] == "created"
    assert upsert_payload["revision"] == 1
    assert isinstance(upsert_payload["updated_at"], str)

    show = _run_cli(
        ["strategy", "show", "--strategy-id", "main", "--json"],
        cwd=tmp_path,
    )
    assert show.returncode == 0, show.stderr
    show_payload = json.loads(show.stdout)
    assert show_payload["strategy_id"] == "main"
    assert show_payload["revision"] == 1
    assert show_payload["strategy"] == _strategy_payload()


def test_strategy_upsert_idempotent_revision(tmp_path: Path) -> None:
    first = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    second = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["revision"] == 1
    assert json.loads(second.stdout)["result"] == "updated"


def test_strategy_list_multiple(tmp_path: Path) -> None:
    for strategy_id in ("s1", "s2"):
        completed = _run_cli(
            ["strategy", "upsert", "--strategy-id", strategy_id, "--input", "-", "--json"],
            cwd=tmp_path,
            input_text=json.dumps(_strategy_payload()),
        )
        assert completed.returncode == 0, completed.stderr

    listed = _run_cli(["strategy", "list", "--json"], cwd=tmp_path)
    assert listed.returncode == 0, listed.stderr
    payload = json.loads(listed.stdout)
    ids = [item["strategy_id"] for item in payload["strategies"]]
    assert ids == ["s1", "s2"]


def test_log_append_and_tail(tmp_path: Path) -> None:
    created = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert created.returncode == 0, created.stderr

    log_ids: list[str] = []
    for step in (1, 2, 3):
        appended = _run_cli(
            ["log", "append", "--strategy-id", "main", "--input", "-", "--json"],
            cwd=tmp_path,
            input_text=json.dumps({"step": step}),
        )
        assert appended.returncode == 0, appended.stderr
        payload = json.loads(appended.stdout)
        log_ids.append(payload["log_id"])

    tail = _run_cli(
        ["log", "tail", "--strategy-id", "main", "--limit", "2", "--json"],
        cwd=tmp_path,
    )
    assert tail.returncode == 0, tail.stderr
    tail_payload = json.loads(tail.stdout)
    assert [row["log_id"] for row in tail_payload["logs"]] == log_ids[-2:]


def test_log_append_missing_strategy_returns_expected_error(tmp_path: Path) -> None:
    completed = _run_cli(
        ["log", "append", "--strategy-id", "missing", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps({"event": "x"}),
    )
    assert completed.returncode == 4
    _assert_error_payload(completed.stderr, code="strategy_not_found")


def test_evaluate_point_uses_strategy_id_and_returns_schema_valid_json(tmp_path: Path) -> None:
    created = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert created.returncode == 0, created.stderr

    request_payload = {"timestamp": "2026-01-01T00:00:00Z", "price": 45_000}
    completed = _run_cli(
        [
            "evaluate-point",
            "--strategy-id",
            "main",
            "--input",
            "-",
            "--output",
            "-",
            "--json",
        ],
        cwd=tmp_path,
        input_text=json.dumps(request_payload),
    )
    assert completed.returncode == 0, completed.stderr
    response = json.loads(completed.stdout)
    validate(
        instance=response,
        schema=_load_json(SCHEMAS / "evaluate_point.response.v1.json"),
        format_checker=FORMAT_CHECKER,
    )


def test_cli_error_codes_and_error_json_format(tmp_path: Path) -> None:
    bad_args = _run_cli(["strategy", "list"], cwd=tmp_path)
    assert bad_args.returncode == 2
    _assert_error_payload(bad_args.stderr, code="invalid_arguments")

    bad_json = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text="{",
    )
    assert bad_json.returncode == 3
    _assert_error_payload(bad_json.stderr, code="io_error")

    bad_schema = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps({"market_mode": "sideways", "price_segments": []}),
    )
    assert bad_schema.returncode == 4
    _assert_error_payload(bad_schema.stderr, code="validation_error")


def test_log_list_rejects_timezone_less_from_ts(tmp_path: Path) -> None:
    created = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert created.returncode == 0, created.stderr

    appended = _run_cli(
        ["log", "append", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps({"event": "x"}),
    )
    assert appended.returncode == 0, appended.stderr

    listed = _run_cli(
        [
            "log",
            "list",
            "--strategy-id",
            "main",
            "--from-ts",
            "2026-01-01T00:00:00",
            "--json",
        ],
        cwd=tmp_path,
    )
    assert listed.returncode == 4
    _assert_error_payload(listed.stderr, code="validation_error")


def test_strategy_upsert_directory_conflict_is_storage_error(tmp_path: Path) -> None:
    strategies_dir = tmp_path / ".psa" / "strategies"
    strategies_dir.mkdir(parents=True, exist_ok=True)
    (strategies_dir / "main").write_text("conflict", encoding="utf-8")

    upsert = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert upsert.returncode == 4
    _assert_error_payload(upsert.stderr, code="storage_error")


def test_strategy_list_root_conflict_is_storage_error(tmp_path: Path) -> None:
    psa_dir = tmp_path / ".psa"
    psa_dir.mkdir(parents=True, exist_ok=True)
    (psa_dir / "strategies").write_text("not-a-directory", encoding="utf-8")

    listed = _run_cli(["strategy", "list", "--json"], cwd=tmp_path)
    assert listed.returncode == 4
    _assert_error_payload(listed.stderr, code="storage_error")


def test_log_list_invalid_stored_ts_is_storage_corrupted(tmp_path: Path) -> None:
    created = _run_cli(
        ["strategy", "upsert", "--strategy-id", "main", "--input", "-", "--json"],
        cwd=tmp_path,
        input_text=json.dumps(_strategy_payload()),
    )
    assert created.returncode == 0, created.stderr

    log_path = tmp_path / ".psa" / "strategies" / "main" / "log.ndjson"
    log_path.write_text(
        '{"log_id":"bad","strategy_id":"main","ts":"2026-01-01T00:00:00","payload":{}}\n',
        encoding="utf-8",
    )

    listed = _run_cli(
        ["log", "list", "--strategy-id", "main", "--json"],
        cwd=tmp_path,
    )
    assert listed.returncode == 4
    _assert_error_payload(listed.stderr, code="storage_corrupted")
