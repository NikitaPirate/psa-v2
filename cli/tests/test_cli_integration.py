from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    pythonpath_parts = [str(ROOT / "cli" / "src"), str(ROOT / "core" / "src")]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return subprocess.run(
        [sys.executable, "-m", "psa_cli", *args],
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


def _decode_envelope(raw: str) -> dict:
    return json.loads(raw)


def _base_strategy_spec() -> dict:
    return {
        "market_mode": "bear",
        "price_segments": [
            {"price_low": 50000, "price_high": 60000, "weight": 10},
            {"price_low": 40000, "price_high": 50000, "weight": 30},
            {"price_low": 30000, "price_high": 40000, "weight": 40},
            {"price_low": 25000, "price_high": 30000, "weight": 20},
        ],
        "time_segments": [
            {
                "start_ts": "2026-01-01T00:00:00Z",
                "end_ts": "2026-06-01T00:00:00Z",
                "k_start": 1.0,
                "k_end": 1.8,
            }
        ],
    }


def _create_strategy_pack_payload() -> dict:
    return {
        "thesis": {
            "id": "thesis-1",
            "title": "Weak market accumulation",
            "summary": "Base thesis",
            "assumptions": ["cycle persists"],
            "invalidation_signals": ["structural break"],
            "horizon": "2026-12-31",
            "status": "active",
        },
        "strategy": {
            "id": "strategy-1",
            "name": "Base bear strategy",
            "objective": "Accumulate with discipline",
            "market_mode": "bear",
            "notes": "initial",
            "status": "active",
        },
        "version": {
            "id": "version-1",
            "label": "v1",
            "rationale": "initial version",
            "created_by": "test",
            "strategy_spec": _base_strategy_spec(),
        },
        "link": {"rationale": "thesis drives strategy"},
        "set_active": True,
    }


def test_show_runtime_returns_success_envelope(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    completed = _run_cli(["--db-path", str(db), "show", "runtime"])
    assert completed.returncode == 0, completed.stderr

    envelope = _decode_envelope(completed.stdout)
    assert envelope["ok"] is True
    assert envelope["result"]["command"] == "show runtime"
    assert envelope["result"]["runtime"]["command"] == "psa"


def test_create_strategy_pack_and_show_summary(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    payload = json.dumps(_create_strategy_pack_payload())

    created = _run_cli(["--db-path", str(db), "create", "strategy-pack", "--json", payload])
    assert created.returncode == 0, created.stderr
    created_data = _decode_envelope(created.stdout)
    assert created_data["ok"] is True
    assert created_data["result"]["result"]["strategy_id"] == "strategy-1"

    summary = _run_cli(["--db-path", str(db), "show", "memory", "--view", "summary"])
    assert summary.returncode == 0, summary.stderr
    summary_data = _decode_envelope(summary.stdout)
    memory = summary_data["result"]["memory"]
    assert memory["counts"]["strategies"] == 1
    assert memory["counts"]["strategy_versions"] == 1
    assert memory["active_strategy"]["id"] == "strategy-1"


def test_update_strategy_pack_adds_version_and_keeps_history(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    create_payload = json.dumps(_create_strategy_pack_payload())
    created = _run_cli(["--db-path", str(db), "create", "strategy-pack", "--json", create_payload])
    assert created.returncode == 0, created.stderr

    updated_spec = _base_strategy_spec()
    updated_spec["time_segments"][0]["k_end"] = 2.0

    update_payload = {
        "strategy": {
            "id": "strategy-1",
            "notes": "revision",
        },
        "version": {
            "id": "version-2",
            "strategy_id": "strategy-1",
            "label": "v2",
            "rationale": "increase acceleration",
            "created_by": "test",
            "strategy_spec": updated_spec,
        },
        "set_active": True,
    }

    updated = _run_cli(
        [
            "--db-path",
            str(db),
            "update",
            "strategy-pack",
            "--json",
            json.dumps(update_payload),
        ]
    )
    assert updated.returncode == 0, updated.stderr

    strategy = _run_cli(
        [
            "--db-path",
            str(db),
            "show",
            "strategy",
            "--id",
            "strategy-1",
            "--include",
            "versions",
        ]
    )
    assert strategy.returncode == 0, strategy.stderr
    strategy_data = _decode_envelope(strategy.stdout)
    versions = strategy_data["result"]["data"]["versions"]
    assert len(versions) == 2
    version_ids = {item["id"] for item in versions}
    assert version_ids == {"version-1", "version-2"}


def test_evaluate_point_inline_and_version_mode(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "create",
            "strategy-pack",
            "--json",
            json.dumps(_create_strategy_pack_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    by_version = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "point",
            "--version-id",
            "version-1",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
        ]
    )
    assert by_version.returncode == 0, by_version.stderr
    by_version_data = _decode_envelope(by_version.stdout)
    assert by_version_data["result"]["strategy_source"] == "version:version-1"
    assert "row" in by_version_data["result"]["data"]

    inline = _run_cli(
        [
            "evaluate",
            "point",
            "--market-mode",
            "bear",
            "--price-segment",
            "50000:60000:10",
            "--price-segment",
            "40000:50000:30",
            "--price-segment",
            "30000:40000:40",
            "--price-segment",
            "25000:30000:20",
            "--time-segment",
            "2026-01-01T00:00:00Z:2026-06-01T00:00:00Z:1.0:1.8",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
        ]
    )
    assert inline.returncode == 0, inline.stderr
    inline_data = _decode_envelope(inline.stdout)
    assert inline_data["result"]["strategy_source"] == "inline"
    assert "row" in inline_data["result"]["data"]


def test_evaluate_rows_and_ranges_by_version(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "create",
            "strategy-pack",
            "--json",
            json.dumps(_create_strategy_pack_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    rows = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "rows",
            "--version-id",
            "version-1",
            "--row",
            "2026-02-01T00:00:00Z:47000",
            "--row",
            "2026-03-01T00:00:00Z:44000",
        ]
    )
    assert rows.returncode == 0, rows.stderr
    rows_data = _decode_envelope(rows.stdout)
    assert len(rows_data["result"]["data"]["rows"]) == 2

    ranges = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "ranges",
            "--version-id",
            "version-1",
            "--price-start",
            "60000",
            "--price-end",
            "25000",
            "--price-steps",
            "4",
            "--time-start",
            "2026-02-01T00:00:00Z",
            "--time-end",
            "2026-04-01T00:00:00Z",
            "--time-steps",
            "3",
            "--include-price-breakpoints",
        ]
    )
    assert ranges.returncode == 0, ranges.stderr
    ranges_data = _decode_envelope(ranges.stdout)
    assert len(ranges_data["result"]["data"]["rows"]) > 0


def test_state_error_returns_code_5_and_error_envelope(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    completed = _run_cli(["--db-path", str(db), "show", "strategy", "--id", "missing"]) 
    assert completed.returncode == 5

    envelope = _decode_envelope(completed.stderr)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "strategy_not_found"


def test_argument_error_returns_code_2_and_error_envelope() -> None:
    completed = _run_cli(["evaluate", "point", "--price", "42000"]) 
    assert completed.returncode == 2

    envelope = _decode_envelope(completed.stderr)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "arguments_error"
