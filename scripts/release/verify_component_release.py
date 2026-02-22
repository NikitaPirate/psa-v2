from __future__ import annotations

import argparse
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CORE_PACKAGE_NAME = "psa-strategy-core"
CLI_PACKAGE_NAME = "psa-strategy-cli"

CORE_TAG_PATTERN = re.compile(r"^core-v(?P<version>\d+\.\d+\.\d+)$")
CLI_TAG_PATTERN = re.compile(r"^cli-v(?P<version>\d+\.\d+\.\d+)$")
BOUND_VERSION_PATTERN = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?$")


@dataclass(frozen=True)
class ComponentReleaseTag:
    component: str
    version: str


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
        if isinstance(dependency, str) and dependency.startswith(CORE_PACKAGE_NAME)
    ]
    if len(core_dependencies) != 1:
        raise SystemExit(
            f"expected exactly one '{CORE_PACKAGE_NAME}' dependency in {pyproject_path}, "
            f"found {len(core_dependencies)}"
        )
    return core_dependencies[0]


def _parse_tag(tag: str) -> ComponentReleaseTag:
    core_match = CORE_TAG_PATTERN.fullmatch(tag)
    if core_match is not None:
        return ComponentReleaseTag(component="core", version=core_match.group("version"))

    cli_match = CLI_TAG_PATTERN.fullmatch(tag)
    if cli_match is not None:
        return ComponentReleaseTag(component="cli", version=cli_match.group("version"))

    raise SystemExit(f"tag '{tag}' must match core-vX.Y.Z or cli-vX.Y.Z")


def _parse_bound_version(version: str) -> tuple[int, int, int | None]:
    match = BOUND_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise SystemExit(
            f"unsupported version bound '{version}'; expected MAJOR.MINOR or MAJOR.MINOR.PATCH"
        )
    patch = match.group("patch")
    return int(match.group("major")), int(match.group("minor")), int(patch) if patch else None


def validate_cli_core_dependency(dependency: str) -> str:
    normalized = dependency.replace(" ", "")
    if not normalized.startswith(CORE_PACKAGE_NAME):
        raise SystemExit(f"dependency '{dependency}' must start with '{CORE_PACKAGE_NAME}'")

    spec = normalized[len(CORE_PACKAGE_NAME) :]
    if not spec:
        raise SystemExit(
            f"dependency '{dependency}' must define compatibility range for '{CORE_PACKAGE_NAME}'"
        )
    if "==" in spec:
        raise SystemExit(
            f"exact pin is not allowed for '{CORE_PACKAGE_NAME}': '{dependency}'. "
            "Use a compatibility range."
        )

    lower_bound: str | None = None
    upper_bound: str | None = None
    for item in spec.split(","):
        if not item:
            continue
        if item.startswith(">="):
            if lower_bound is not None:
                raise SystemExit(f"multiple lower bounds are not allowed: '{dependency}'")
            lower_bound = item[2:]
            continue
        if item.startswith("<") and not item.startswith("<="):
            if upper_bound is not None:
                raise SystemExit(f"multiple upper bounds are not allowed: '{dependency}'")
            upper_bound = item[1:]
            continue
        raise SystemExit(
            f"unsupported comparator in '{dependency}'. "
            "Only '>=' lower bound and '<' upper bound are allowed."
        )

    if lower_bound is None or upper_bound is None:
        raise SystemExit(
            f"dependency '{dependency}' must include both '>=' lower and '<' upper bounds"
        )

    lower_major, lower_minor, _ = _parse_bound_version(lower_bound)
    upper_major, upper_minor, upper_patch = _parse_bound_version(upper_bound)

    if lower_major == 0:
        expected_upper = (0, lower_minor + 1)
    else:
        expected_upper = (lower_major + 1, 0)

    if (upper_major, upper_minor) != expected_upper:
        raise SystemExit(
            "invalid core dependency upper bound for CLI: "
            f"lower>={lower_major}.{lower_minor}, upper<{upper_major}.{upper_minor}; "
            f"expected upper<{expected_upper[0]}.{expected_upper[1]}"
        )
    if upper_patch not in (None, 0):
        raise SystemExit(
            f"invalid upper bound '{upper_bound}': patch boundary must be omitted or 0"
        )

    return f"{CORE_PACKAGE_NAME}>={lower_bound},<{upper_bound}"


def validate_component_release_state(tag: str, repo_root: Path) -> str:
    parsed_tag = _parse_tag(tag)
    core_pyproject = repo_root / "core" / "pyproject.toml"
    cli_pyproject = repo_root / "cli" / "pyproject.toml"

    if parsed_tag.component == "core":
        core_version = _extract_version(core_pyproject)
        if core_version != parsed_tag.version:
            raise SystemExit(
                f"core version mismatch: tag={parsed_tag.version}, core={core_version}"
            )
        return f"release state ok: component=core, tag={tag}, version={core_version}"

    cli_version = _extract_version(cli_pyproject)
    if cli_version != parsed_tag.version:
        raise SystemExit(f"cli version mismatch: tag={parsed_tag.version}, cli={cli_version}")

    core_dependency = _extract_cli_core_dependency(cli_pyproject)
    normalized_dependency = validate_cli_core_dependency(core_dependency)
    return (
        f"release state ok: component=cli, tag={tag}, version={cli_version}, "
        f"dependency={normalized_dependency}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            f"Validate component release tags and dependency policy for {CORE_PACKAGE_NAME} "
            f"and {CLI_PACKAGE_NAME}."
        )
    )
    parser.add_argument(
        "--tag",
        required=True,
        help="Component tag, for example core-v0.2.0 or cli-v0.3.1",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Repository root path. Defaults to this script's repository root.",
    )
    args = parser.parse_args()

    message = validate_component_release_state(args.tag, Path(args.repo_root))
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
