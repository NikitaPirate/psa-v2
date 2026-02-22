from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "release" / "verify_component_release.py"


def _load_release_module():
    spec = importlib.util.spec_from_file_location("verify_component_release", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load module spec from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_pyproject(path: Path, *, name: str, version: str, dependencies: list[str]) -> None:
    rendered_dependencies = ",\n".join(f'    "{item}"' for item in dependencies)
    path.write_text(
        "\n".join(
            [
                "[project]",
                f'name = "{name}"',
                f'version = "{version}"',
                "dependencies = [",
                rendered_dependencies,
                "]",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _create_repo(
    tmp_path: Path,
    *,
    core_version: str = "0.1.0",
    cli_version: str = "0.1.0",
    cli_dependency: str = "psa-strategy-core>=0.1,<0.2",
) -> Path:
    (tmp_path / "core").mkdir()
    (tmp_path / "cli").mkdir()
    _write_pyproject(
        tmp_path / "core" / "pyproject.toml",
        name="psa-strategy-core",
        version=core_version,
        dependencies=[],
    )
    _write_pyproject(
        tmp_path / "cli" / "pyproject.toml",
        name="psa-strategy-cli",
        version=cli_version,
        dependencies=["jsonschema>=4.25.0", cli_dependency],
    )
    return tmp_path


def test_core_release_tag_matches_core_version(tmp_path: Path) -> None:
    module = _load_release_module()
    repo_root = _create_repo(tmp_path, core_version="0.2.0")

    result = module.validate_component_release_state("core-v0.2.0", repo_root)

    assert "component=core" in result
    assert "version=0.2.0" in result


def test_core_release_fails_on_version_mismatch(tmp_path: Path) -> None:
    module = _load_release_module()
    repo_root = _create_repo(tmp_path, core_version="0.2.0")

    with pytest.raises(SystemExit, match="core version mismatch"):
        module.validate_component_release_state("core-v0.2.1", repo_root)


def test_cli_release_tag_matches_cli_version_and_range_dependency(tmp_path: Path) -> None:
    module = _load_release_module()
    repo_root = _create_repo(
        tmp_path,
        cli_version="0.5.0",
        cli_dependency="psa-strategy-core>=0.1,<0.2",
    )

    result = module.validate_component_release_state("cli-v0.5.0", repo_root)

    assert "component=cli" in result
    assert "version=0.5.0" in result


def test_cli_release_fails_for_exact_core_pin(tmp_path: Path) -> None:
    module = _load_release_module()
    repo_root = _create_repo(
        tmp_path,
        cli_version="0.5.0",
        cli_dependency="psa-strategy-core==0.1.0",
    )

    with pytest.raises(SystemExit, match="exact pin is not allowed"):
        module.validate_component_release_state("cli-v0.5.0", repo_root)
