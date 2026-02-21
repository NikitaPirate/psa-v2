from __future__ import annotations

import json
from pathlib import Path

import psa_cli.schema as schema_module


class _FakeResourceFile:
    def __init__(self, text: str | None) -> None:
        self._text = text

    def is_file(self) -> bool:
        return self._text is not None

    def read_text(self, *, encoding: str = "utf-8") -> str:
        assert encoding == "utf-8"
        if self._text is None:
            raise FileNotFoundError("missing resource")
        return self._text


class _FakeResourceRoot:
    def __init__(self, files_map: dict[str, str]) -> None:
        self._files_map = files_map

    def joinpath(self, *parts: str) -> _FakeResourceFile:
        key = "/".join(parts)
        return _FakeResourceFile(self._files_map.get(key))


def _write_schema(directory: Path, schema_file: str, *, marker: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    schema = {"type": "object", "title": marker}
    (directory / schema_file).write_text(json.dumps(schema), encoding="utf-8")


def test_load_schema_prioritizes_env_over_packaged_and_repo(
    monkeypatch, tmp_path: Path
) -> None:
    schema_module.load_schema.cache_clear()
    schema_file = "evaluate_point.request.v1.json"

    env_dir = tmp_path / "env"
    repo_dir = tmp_path / "repo"
    _write_schema(env_dir, schema_file, marker="env")
    _write_schema(repo_dir, schema_file, marker="repo")

    monkeypatch.setenv("PSA_SCHEMA_DIR", str(env_dir))
    monkeypatch.setattr(
        schema_module,
        "_schema_candidates",
        lambda: [("PSA_SCHEMA_DIR", env_dir), ("repo", repo_dir)],
    )
    monkeypatch.setattr(
        schema_module,
        "files",
        lambda _: _FakeResourceRoot(
            {"schemas/evaluate_point.request.v1.json": json.dumps({"title": "packaged"})}
        ),
    )

    loaded = schema_module.load_schema(schema_file)
    assert loaded["title"] == "env"


def test_load_schema_uses_packaged_before_repo(monkeypatch, tmp_path: Path) -> None:
    schema_module.load_schema.cache_clear()
    schema_file = "evaluate_point.request.v1.json"

    repo_dir = tmp_path / "repo"
    _write_schema(repo_dir, schema_file, marker="repo")

    monkeypatch.delenv("PSA_SCHEMA_DIR", raising=False)
    monkeypatch.setattr(schema_module, "_schema_candidates", lambda: [("repo", repo_dir)])
    monkeypatch.setattr(
        schema_module,
        "files",
        lambda _: _FakeResourceRoot(
            {"schemas/evaluate_point.request.v1.json": json.dumps({"title": "packaged"})}
        ),
    )

    loaded = schema_module.load_schema(schema_file)
    assert loaded["title"] == "packaged"


def test_load_schema_falls_back_to_repo_when_packaged_missing(
    monkeypatch, tmp_path: Path
) -> None:
    schema_module.load_schema.cache_clear()
    schema_file = "evaluate_point.request.v1.json"

    repo_dir = tmp_path / "repo"
    _write_schema(repo_dir, schema_file, marker="repo")

    monkeypatch.delenv("PSA_SCHEMA_DIR", raising=False)
    monkeypatch.setattr(schema_module, "_schema_candidates", lambda: [("repo", repo_dir)])
    monkeypatch.setattr(schema_module, "files", lambda _: _FakeResourceRoot({}))

    loaded = schema_module.load_schema(schema_file)
    assert loaded["title"] == "repo"


def test_validate_request_accepts_strategy_upsert_payload() -> None:
    schema_module.load_schema.cache_clear()
    payload = {
        "market_mode": "bear",
        "price_segments": [{"price_low": 1.0, "price_high": 2.0, "weight": 100.0}],
    }
    schema_module.validate_request("strategy-upsert", payload)


def test_validate_request_rejects_evaluate_point_with_inline_strategy() -> None:
    schema_module.load_schema.cache_clear()
    payload = {
        "strategy": {
            "market_mode": "bear",
            "price_segments": [{"price_low": 1.0, "price_high": 2.0, "weight": 100.0}],
        },
        "timestamp": "2026-01-01T00:00:00Z",
        "price": 1.0,
    }
    try:
        schema_module.validate_request("evaluate-point", payload)
    except Exception as exc:
        assert "request does not match schema" in str(exc)
    else:
        raise AssertionError("expected schema validation failure")
