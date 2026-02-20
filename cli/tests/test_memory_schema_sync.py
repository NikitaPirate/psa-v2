from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from psa_cli.store import MemoryStore

ROOT = Path(__file__).resolve().parents[2]
MEMORY_SCHEMA = ROOT / "skills" / "psa-strategist" / "references" / "memory-schema-v1.json"
FORMAT_CHECKER = FormatChecker()


def _load_memory_schema() -> dict:
    return json.loads(MEMORY_SCHEMA.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_memory_schema(), format_checker=FORMAT_CHECKER)


def test_default_store_matches_skill_memory_schema(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "memory.json")
    snapshot = store.get_full_store(create_if_missing=True)
    _validator().validate(snapshot)


def test_saved_strategy_state_matches_skill_memory_schema(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "memory.json")

    store.apply_batch(
        [
            {
                "op": "upsert_thesis",
                "thesis": {
                    "id": "thesis-1",
                    "title": "Weak market accumulation",
                    "summary": "Expect prolonged weakness before recovery.",
                    "assumptions": ["cycle persists"],
                    "invalidation_signals": ["macro regime shift"],
                    "horizon": "2026-12-31",
                    "status": "active",
                },
            },
            {
                "op": "upsert_strategy",
                "strategy": {
                    "id": "strategy-1",
                    "name": "Base strategy",
                    "objective": "Accumulate in bear mode",
                    "market_mode": "bear",
                    "notes": "initial",
                    "status": "active",
                },
            },
            {
                "op": "add_strategy_version",
                "version": {
                    "id": "version-1",
                    "strategy_id": "strategy-1",
                    "label": "v1",
                    "rationale": "initial setup",
                    "created_by": "test",
                    "strategy_spec": {
                        "market_mode": "bear",
                        "price_segments": [
                            {"price_low": 50_000, "price_high": 60_000, "weight": 10},
                            {"price_low": 40_000, "price_high": 50_000, "weight": 30},
                        ],
                        "time_segments": [
                            {
                                "start_ts": "2026-01-01T00:00:00Z",
                                "end_ts": "2026-06-01T00:00:00Z",
                                "k_start": 1.0,
                                "k_end": 1.8,
                            }
                        ],
                    },
                    "tags": ["base"],
                },
            },
            {
                "op": "link_strategy_thesis",
                "link": {
                    "strategy_id": "strategy-1",
                    "thesis_id": "thesis-1",
                    "rationale": "thesis drives strategy",
                },
            },
            {"op": "set_active_strategy", "strategy_id": "strategy-1"},
        ],
    )

    snapshot = store.get_full_store(create_if_missing=False)
    _validator().validate(snapshot)
