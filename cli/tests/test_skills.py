from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from psa_cli.errors import CliIoError, CliValidationError
from psa_cli.skills import RUNTIME_CONFIG, install_skill


@pytest.fixture
def clean_skill_dest(tmp_path: Path) -> None:
    for config in RUNTIME_CONFIG.values():
        skills_dir = tmp_path / config["skills_dir"].lstrip("~/")
        if skills_dir.exists():
            shutil.rmtree(skills_dir)


def test_runtime_config_has_expected_runtimes():
    expected = {"claude", "codex", "opencode", "gemini", "cursor", "windsurf", "qwen"}
    assert expected.issubset(RUNTIME_CONFIG.keys())


def test_install_skill_invalid_runtime():
    with pytest.raises(CliValidationError) as exc_info:
        install_skill("invalid-runtime")
    assert "unknown runtime" in str(exc_info.value)


def test_install_skill_claude(tmp_path: Path, clean_skill_dest: None):
    result = install_skill("claude", home_dir=tmp_path)

    assert result["runtime"] == "claude"
    assert result["skill"] == "psa-strategist"
    assert result["files_installed"] > 0
    assert result["files_skipped"] == 0

    dest = Path(result["dest"])
    assert dest.exists()
    assert (dest / "SKILL.md").exists()
    assert (dest / "references").is_dir()


def test_install_skill_codex_includes_agents_config(tmp_path: Path, clean_skill_dest: None):
    result = install_skill("codex", home_dir=tmp_path)

    assert result["runtime"] == "codex"
    assert Path(result["dest"]) == tmp_path / ".codex" / "skills" / "psa-strategist"
    assert "agents_config" in result
    agents_cfg = result["agents_config"]
    assert agents_cfg["status"] == "installed"
    assert Path(agents_cfg["path"]).exists()
    assert Path(agents_cfg["path"]) == tmp_path / ".codex" / "agents" / "psa-strategist.yaml"


def test_install_skill_idempotent(tmp_path: Path, clean_skill_dest: None):
    result1 = install_skill("claude", home_dir=tmp_path)
    result2 = install_skill("claude", home_dir=tmp_path)

    assert result1["files_installed"] > 0
    assert result1["files_skipped"] == 0

    assert result2["files_installed"] == 0
    assert result2["files_skipped"] > 0


def test_install_skill_via_cli(
    tmp_path: Path, clean_skill_dest: None, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    from psa_cli.app import main

    exit_code = main(["install-skill", "opencode", "--json"])
    assert exit_code == 0

    dest = tmp_path / ".opencode" / "skills" / "psa-strategist"
    assert dest.exists()
    assert (dest / "SKILL.md").exists()


def test_install_skill_maps_copy_oserror_to_cli_io_error(
    tmp_path: Path, clean_skill_dest: None, monkeypatch: pytest.MonkeyPatch
):
    def _raise_oserror(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(shutil, "copy2", _raise_oserror)

    with pytest.raises(CliIoError) as exc_info:
        install_skill("claude", home_dir=tmp_path)
    assert "failed to copy" in str(exc_info.value)
