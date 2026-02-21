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


def _upsert_strategy_state_payload() -> dict:
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


def test_upsert_strategy_state_and_show_summary(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    payload = json.dumps(_upsert_strategy_state_payload())

    created = _run_cli(["--db-path", str(db), "upsert", "strategy-state", "--json", payload])
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


def test_upsert_strategy_state_revision_adds_version_and_keeps_history(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    create_payload = json.dumps(_upsert_strategy_state_payload())
    created = _run_cli(["--db-path", str(db), "upsert", "strategy-state", "--json", create_payload])
    assert created.returncode == 0, created.stderr

    updated_spec = _base_strategy_spec()
    updated_spec["time_segments"][0]["k_end"] = 2.0

    update_payload = {
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
            "upsert",
            "strategy-state",
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


def test_evaluate_point_uses_latest_by_default_and_version_override(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy-state",
            "--json",
            json.dumps(_upsert_strategy_state_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    latest = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "point",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
        ]
    )
    assert latest.returncode == 0, latest.stderr
    latest_data = _decode_envelope(latest.stdout)
    assert latest_data["result"]["strategy_source"] == "latest:strategy-1:version-1"
    assert "row" in latest_data["result"]["data"]

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


def test_evaluate_rows_and_ranges_with_latest_strategy(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy-state",
            "--json",
            json.dumps(_upsert_strategy_state_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    rows = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "rows",
            "--row",
            "2026-02-01T00:00:00Z:47000",
            "--row",
            "2026-03-01T00:00:00Z:44000",
        ]
    )
    assert rows.returncode == 0, rows.stderr
    rows_data = _decode_envelope(rows.stdout)
    assert rows_data["result"]["strategy_source"] == "latest:strategy-1:version-1"
    assert len(rows_data["result"]["data"]["rows"]) == 2

    ranges = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "ranges",
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
    assert ranges_data["result"]["strategy_source"] == "latest:strategy-1:version-1"
    assert len(ranges_data["result"]["data"]["rows"]) > 0


def test_upsert_checkin_and_decision_are_idempotent_by_id(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy-state",
            "--json",
            json.dumps(_upsert_strategy_state_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    checkin_first = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "checkin",
            "--id",
            "checkin-1",
            "--strategy-id",
            "strategy-1",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
            "--note",
            "first",
        ]
    )
    assert checkin_first.returncode == 0, checkin_first.stderr
    checkin_retry = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "checkin",
            "--id",
            "checkin-1",
            "--strategy-id",
            "strategy-1",
            "--note",
            "retry-note",
        ]
    )
    assert checkin_retry.returncode == 0, checkin_retry.stderr

    checkins = _run_cli(["--db-path", str(db), "show", "checkins", "--strategy-id", "strategy-1"])
    assert checkins.returncode == 0, checkins.stderr
    checkins_data = _decode_envelope(checkins.stdout)
    assert checkins_data["result"]["count"] == 1
    assert checkins_data["result"]["checkins"][0]["id"] == "checkin-1"
    assert checkins_data["result"]["checkins"][0]["note"] == "retry-note"

    decision_first = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "decision",
            "--id",
            "decision-1",
            "--strategy-id",
            "strategy-1",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--action-summary",
            "hold",
            "--rationale",
            "initial",
        ]
    )
    assert decision_first.returncode == 0, decision_first.stderr
    decision_retry = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "decision",
            "--id",
            "decision-1",
            "--strategy-id",
            "strategy-1",
            "--action-summary",
            "hold",
            "--rationale",
            "retry-update",
        ]
    )
    assert decision_retry.returncode == 0, decision_retry.stderr

    decisions = _run_cli(["--db-path", str(db), "show", "decisions", "--strategy-id", "strategy-1"])
    assert decisions.returncode == 0, decisions.stderr
    decisions_data = _decode_envelope(decisions.stdout)
    assert decisions_data["result"]["count"] == 1
    assert decisions_data["result"]["decisions"][0]["id"] == "decision-1"
    assert decisions_data["result"]["decisions"][0]["rationale"] == "retry-update"


def test_upsert_checkin_fails_on_legacy_duplicate_ids(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy-state",
            "--json",
            json.dumps(_upsert_strategy_state_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    store_payload = json.loads(db.read_text(encoding="utf-8"))
    store_payload["checkins"] = [
        {
            "id": "dup-checkin-1",
            "strategy_id": "strategy-1",
            "timestamp": "2026-03-01T00:00:00Z",
            "price": 42000,
            "context": "legacy-1",
            "evaluation": {},
            "note": "legacy-1",
            "created_at": "2026-03-01T00:00:00Z",
        },
        {
            "id": "dup-checkin-1",
            "strategy_id": "strategy-1",
            "timestamp": "2026-03-02T00:00:00Z",
            "price": 41900,
            "context": "legacy-2",
            "evaluation": {},
            "note": "legacy-2",
            "created_at": "2026-03-02T00:00:00Z",
        },
    ]
    db.write_text(json.dumps(store_payload), encoding="utf-8")

    completed = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "checkin",
            "--id",
            "dup-checkin-1",
            "--strategy-id",
            "strategy-1",
            "--note",
            "retry",
        ]
    )
    assert completed.returncode == 5
    envelope = _decode_envelope(completed.stderr)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "checkin_conflict_duplicate_id"


def test_upsert_decision_fails_on_legacy_duplicate_ids(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy-state",
            "--json",
            json.dumps(_upsert_strategy_state_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    store_payload = json.loads(db.read_text(encoding="utf-8"))
    store_payload["decision_log"] = [
        {
            "id": "dup-decision-1",
            "strategy_id": "strategy-1",
            "timestamp": "2026-03-01T00:00:00Z",
            "action_summary": "hold",
            "rationale": "legacy-1",
            "linked_checkin_id": None,
            "created_at": "2026-03-01T00:00:00Z",
        },
        {
            "id": "dup-decision-1",
            "strategy_id": "strategy-1",
            "timestamp": "2026-03-02T00:00:00Z",
            "action_summary": "hold",
            "rationale": "legacy-2",
            "linked_checkin_id": None,
            "created_at": "2026-03-02T00:00:00Z",
        },
    ]
    db.write_text(json.dumps(store_payload), encoding="utf-8")

    completed = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "decision",
            "--id",
            "dup-decision-1",
            "--strategy-id",
            "strategy-1",
            "--action-summary",
            "hold",
        ]
    )
    assert completed.returncode == 5
    envelope = _decode_envelope(completed.stderr)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "decision_conflict_duplicate_id"


def test_evaluate_rejects_strategy_id_with_inline_flags(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    created = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy-state",
            "--json",
            json.dumps(_upsert_strategy_state_payload()),
        ]
    )
    assert created.returncode == 0, created.stderr

    completed = _run_cli(
        [
            "--db-path",
            str(db),
            "evaluate",
            "point",
            "--strategy-id",
            "strategy-1",
            "--market-mode",
            "bear",
            "--price-segment",
            "40000:50000:1",
            "--timestamp",
            "2026-03-01T00:00:00Z",
            "--price",
            "42000",
        ]
    )
    assert completed.returncode == 4
    envelope = _decode_envelope(completed.stderr)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "conflicting_strategy_source"


def test_upsert_strategy_set_active_without_explicit_id(tmp_path: Path) -> None:
    db = tmp_path / "memory.json"
    completed = _run_cli(
        [
            "--db-path",
            str(db),
            "upsert",
            "strategy",
            "--name",
            "Generated strategy",
            "--objective",
            "Accumulate",
            "--market-mode",
            "bear",
            "--set-active",
        ]
    )
    assert completed.returncode == 0, completed.stderr
    created = _decode_envelope(completed.stdout)
    strategy_id = created["result"]["result"]["results"][0]["strategy_id"]
    assert isinstance(strategy_id, str) and strategy_id

    summary = _run_cli(["--db-path", str(db), "show", "memory", "--view", "summary"])
    assert summary.returncode == 0, summary.stderr
    summary_data = _decode_envelope(summary.stdout)
    assert summary_data["result"]["memory"]["active_strategy"]["id"] == strategy_id


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
