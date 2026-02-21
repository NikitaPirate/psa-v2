from __future__ import annotations

import time
from multiprocessing import Process
from pathlib import Path

import pytest
from psa_cli.errors import CliDomainError
from psa_cli.locks import exclusive_lock
from psa_cli.store import (
    append_log,
    list_logs,
    show_log,
    strategy_exists,
    tail_logs,
    upsert_strategy,
)


def _hold_lock_for_test(lock_path: str, ready_path: str) -> None:
    lock = Path(lock_path)
    ready = Path(ready_path)
    with exclusive_lock(lock, timeout_seconds=1.0):
        ready.write_text("ready", encoding="utf-8")
        time.sleep(0.5)


def _strategy_payload() -> dict:
    return {
        "market_mode": "bear",
        "price_segments": [{"price_low": 10_000.0, "price_high": 20_000.0, "weight": 100.0}],
        "time_segments": [],
    }


def test_upsert_is_idempotent_for_same_payload(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    created = upsert_strategy("main", _strategy_payload())
    repeated = upsert_strategy("main", _strategy_payload())

    assert created["result"] == "created"
    assert created["revision"] == 1
    assert repeated["result"] == "updated"
    assert repeated["revision"] == 1
    assert strategy_exists("main") is True


def test_append_log_requires_existing_strategy(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(CliDomainError) as excinfo:
        append_log("missing", {"event": "x"})
    assert excinfo.value.error_code == "strategy_not_found"


def test_tail_returns_last_records_in_order(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    upsert_strategy("main", _strategy_payload())

    first = append_log("main", {"step": 1})
    second = append_log("main", {"step": 2})
    third = append_log("main", {"step": 3})

    tail = tail_logs("main", limit=2)
    assert [row["log_id"] for row in tail] == [second["log_id"], third["log_id"]]

    shown = show_log("main", log_id=first["log_id"])
    assert shown["payload"]["step"] == 1

    listed = list_logs("main", limit=2)
    assert len(listed) == 2


def test_exclusive_lock_times_out_when_other_process_holds_lock(tmp_path: Path) -> None:
    lock_path = tmp_path / ".psa" / "strategies" / "main" / ".lock"
    ready_path = tmp_path / "ready"

    process = Process(target=_hold_lock_for_test, args=(str(lock_path), str(ready_path)))
    process.start()
    try:
        for _ in range(50):
            if ready_path.exists():
                break
            time.sleep(0.01)
        with pytest.raises(CliDomainError) as excinfo:
            with exclusive_lock(lock_path, timeout_seconds=0.05):
                pass
        assert excinfo.value.error_code == "lock_timeout"
    finally:
        process.join(timeout=2.0)
        if process.is_alive():
            process.terminate()
            process.join(timeout=2.0)
