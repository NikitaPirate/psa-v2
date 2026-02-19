from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path
from typing import Any

TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")


def _load_project_table(pyproject_path: Path) -> dict[str, Any]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise SystemExit(f"missing [project] in {pyproject_path}")
    return project


def _extract_version(pyproject_path: Path) -> str:
    project = _load_project_table(pyproject_path)
    version = project.get("version")
    if not isinstance(version, str):
        raise SystemExit(f"missing project.version in {pyproject_path}")
    return version


def _extract_cli_core_dependency(pyproject_path: Path) -> str:
    project = _load_project_table(pyproject_path)
    dependencies = project.get("dependencies")
    if not isinstance(dependencies, list):
        raise SystemExit(f"missing project.dependencies in {pyproject_path}")

    core_dependencies = [
        dependency
        for dependency in dependencies
        if isinstance(dependency, str) and dependency.startswith("psa-core")
    ]
    if len(core_dependencies) != 1:
        raise SystemExit(
            f"expected exactly one 'psa-core' dependency in {pyproject_path}, "
            f"found {len(core_dependencies)}"
        )
    return core_dependencies[0]


def _version_from_tag(tag: str) -> str:
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise SystemExit(f"tag '{tag}' must match vX.Y.Z")
    return match.group("version")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate lockstep release versions for psa-core and psa-cli."
    )
    parser.add_argument("--tag", required=True, help="Git tag, for example v0.1.0")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    core_pyproject = repo_root / "core" / "pyproject.toml"
    cli_pyproject = repo_root / "cli" / "pyproject.toml"

    expected_version = _version_from_tag(args.tag)
    core_version = _extract_version(core_pyproject)
    cli_version = _extract_version(cli_pyproject)

    if core_version != expected_version:
        raise SystemExit(
            f"core version mismatch: tag={expected_version}, core={core_version}"
        )
    if cli_version != expected_version:
        raise SystemExit(
            f"cli version mismatch: tag={expected_version}, cli={cli_version}"
        )

    core_dependency = _extract_cli_core_dependency(cli_pyproject)
    expected_dependency = f"psa-core=={expected_version}"
    if core_dependency != expected_dependency:
        raise SystemExit(
            "cli dependency mismatch: "
            f"expected '{expected_dependency}', found '{core_dependency}'"
        )

    print(
        "release state ok: "
        f"tag={args.tag}, core={core_version}, cli={cli_version}, dep={core_dependency}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
