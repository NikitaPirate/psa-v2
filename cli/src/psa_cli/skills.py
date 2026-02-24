from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from psa_cli.errors import CliIoError, CliValidationError

RUNTIME_CONFIG: dict[str, dict[str, Any]] = {
    "any-runtime": {
        "name": "Any Runtime",
    },
    "claude": {
        "name": "Claude Code",
        "skills_dir": "~/.claude/skills",
    },
    "codex": {
        "name": "Codex CLI",
        "skills_dir": "~/.codex/skills",
        "agents_dir": "~/.codex/agents",
    },
    "opencode": {
        "name": "OpenCode",
        "skills_dir": "~/.opencode/skills",
    },
    "openclaw": {
        "name": "OpenClaw",
        "skills_dir": "~/.openclaw/skills",
    },
    "gemini": {
        "name": "Gemini CLI",
        "skills_dir": "~/.gemini/skills",
    },
    "cursor": {
        "name": "Cursor",
        "skills_dir": "~/.cursor/skills",
    },
    "windsurf": {
        "name": "Windsurf",
        "skills_dir": "~/.windsurf/skills",
    },
    "qwen": {
        "name": "Qwen Code",
        "skills_dir": "~/.qwen/skills",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "skills_dir": "~/.github/skills",
    },
    "kilocode": {
        "name": "Kilo Code",
        "skills_dir": "~/.kilocode/skills",
    },
    "auggie": {
        "name": "Auggie CLI",
        "skills_dir": "~/.augment/skills",
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "skills_dir": "~/.codebuddy/skills",
    },
    "qodercli": {
        "name": "Qoder CLI",
        "skills_dir": "~/.qoder/skills",
    },
    "roo": {
        "name": "Roo Code",
        "skills_dir": "~/.roo/skills",
    },
    "q": {
        "name": "Amazon Q Developer CLI",
        "skills_dir": "~/.amazonq/skills",
    },
    "amp": {
        "name": "Amp",
        "skills_dir": "~/.agents/skills",
    },
    "shai": {
        "name": "SHAI",
        "skills_dir": "~/.shai/skills",
    },
    "agy": {
        "name": "Antigravity",
        "skills_dir": "~/.agent/skills",
    },
    "bob": {
        "name": "IBM Bob",
        "skills_dir": "~/.bob/skills",
    },
}

SKILL_NAME = "psa-strategist"


def supported_runtimes() -> tuple[str, ...]:
    return tuple(sorted(RUNTIME_CONFIG.keys()))


def _is_valid_skill_source(path: Path) -> bool:
    return (path / "SKILL.md").is_file()


def _get_skill_source_path() -> Path:
    packaged_path = Path(__file__).parent / "skills" / SKILL_NAME
    if _is_valid_skill_source(packaged_path):
        return packaged_path

    # Dev fallback: in workspace sources the skill lives in repository root `skills/`.
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "skills" / SKILL_NAME
        if _is_valid_skill_source(candidate):
            return candidate

    return packaged_path


def _copy_skill_files(source: Path, dest: Path) -> tuple[int, int]:
    installed = 0
    skipped = 0

    for item in source.rglob("*"):
        if item.is_dir():
            continue

        rel_path = item.relative_to(source)
        dest_file = dest / rel_path

        if dest_file.exists():
            skipped += 1
            continue

        try:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            reason = exc.strerror or str(exc)
            raise CliIoError(f"failed to create directory '{dest_file.parent}': {reason}") from exc

        try:
            shutil.copy2(item, dest_file)
        except OSError as exc:
            reason = exc.strerror or str(exc)
            raise CliIoError(f"failed to copy '{item}' to '{dest_file}': {reason}") from exc
        installed += 1

    return installed, skipped


def _expand_skill_dir(skill_dir: str, home_dir: Path | None = None) -> Path:
    if skill_dir.startswith("~/"):
        base = home_dir if home_dir else Path.home()
        return base / skill_dir[2:]
    return Path(skill_dir)


def _install_agents_config(
    runtime: str,
    home_dir: Path | None = None,
    agents_dir_override: str | None = None,
) -> dict[str, Any] | None:
    config = RUNTIME_CONFIG.get(runtime, {})
    agents_dir = agents_dir_override if agents_dir_override else config.get("agents_dir")
    if not agents_dir:
        return None

    source_yaml = _get_skill_source_path() / "agents" / "openai.yaml"
    if not source_yaml.exists():
        return None

    dest_agents_dir = _expand_skill_dir(agents_dir, home_dir)
    try:
        dest_agents_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise CliIoError(f"failed to create directory '{dest_agents_dir}': {reason}") from exc

    dest_yaml = dest_agents_dir / f"{SKILL_NAME}.yaml"
    if dest_yaml.exists():
        return {"path": str(dest_yaml), "status": "skipped"}

    try:
        shutil.copy2(source_yaml, dest_yaml)
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise CliIoError(f"failed to copy '{source_yaml}' to '{dest_yaml}': {reason}") from exc
    return {"path": str(dest_yaml), "status": "installed"}


def install_skill(
    runtime: str,
    home_dir: Path | None = None,
    skills_dir_override: str | None = None,
    agents_dir_override: str | None = None,
) -> dict[str, Any]:
    if runtime not in RUNTIME_CONFIG:
        valid_runtimes = ", ".join(supported_runtimes())
        raise CliValidationError(f"unknown runtime '{runtime}'. Supported: {valid_runtimes}")

    config = RUNTIME_CONFIG[runtime]
    if runtime == "any-runtime" and not skills_dir_override:
        raise CliValidationError("--skills-dir is required for runtime 'any-runtime'")

    default_skills_dir = config.get("skills_dir")
    resolved_skills_dir = skills_dir_override or default_skills_dir
    if not resolved_skills_dir:
        raise CliValidationError(f"runtime '{runtime}' has no default skills directory")

    skills_dir = _expand_skill_dir(resolved_skills_dir, home_dir)
    dest_skill_dir = skills_dir / SKILL_NAME

    source_path = _get_skill_source_path()
    if not _is_valid_skill_source(source_path):
        raise CliValidationError(f"skill '{SKILL_NAME}' not found in package resources")

    installed, skipped = _copy_skill_files(source_path, dest_skill_dir)

    result: dict[str, Any] = {
        "runtime": runtime,
        "runtime_name": config["name"],
        "skill": SKILL_NAME,
        "dest": str(dest_skill_dir),
        "files_installed": installed,
        "files_skipped": skipped,
    }

    agents_result = _install_agents_config(
        runtime, home_dir, agents_dir_override=agents_dir_override
    )
    if agents_result:
        result["agents_config"] = agents_result

    return result
