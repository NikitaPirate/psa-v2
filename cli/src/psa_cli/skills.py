from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from psa_cli.errors import CliValidationError

RUNTIME_CONFIG: dict[str, dict[str, Any]] = {
    "claude": {
        "name": "Claude Code",
        "skills_dir": "~/.claude/skills",
    },
    "codex": {
        "name": "Codex CLI",
        "skills_dir": "~/.agents/skills",
        "agents_dir": "~/.codex/agents",
    },
    "opencode": {
        "name": "OpenCode",
        "skills_dir": "~/.opencode/skills",
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


def _get_skill_source_path() -> Path:
    return Path(__file__).parent / "skills" / SKILL_NAME


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

        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest_file)
        installed += 1

    return installed, skipped


def _expand_skill_dir(skill_dir: str, home_dir: Path | None = None) -> Path:
    if skill_dir.startswith("~/"):
        base = home_dir if home_dir else Path.home()
        return base / skill_dir[2:]
    return Path(skill_dir)


def _install_agents_config(runtime: str, home_dir: Path | None = None) -> dict[str, Any] | None:
    config = RUNTIME_CONFIG.get(runtime, {})
    agents_dir = config.get("agents_dir")
    if not agents_dir:
        return None

    source_yaml = _get_skill_source_path() / "agents" / "openai.yaml"
    if not source_yaml.exists():
        return None

    dest_agents_dir = _expand_skill_dir(agents_dir, home_dir)
    dest_agents_dir.mkdir(parents=True, exist_ok=True)

    dest_yaml = dest_agents_dir / f"{SKILL_NAME}.yaml"
    if dest_yaml.exists():
        return {"path": str(dest_yaml), "status": "skipped"}

    shutil.copy2(source_yaml, dest_yaml)
    return {"path": str(dest_yaml), "status": "installed"}


def install_skill(runtime: str, home_dir: Path | None = None) -> dict[str, Any]:
    if runtime not in RUNTIME_CONFIG:
        valid_runtimes = ", ".join(sorted(RUNTIME_CONFIG.keys()))
        raise CliValidationError(f"unknown runtime '{runtime}'. Supported: {valid_runtimes}")

    config = RUNTIME_CONFIG[runtime]
    skills_dir = _expand_skill_dir(config["skills_dir"], home_dir)
    dest_skill_dir = skills_dir / SKILL_NAME

    source_path = _get_skill_source_path()
    if not source_path.exists():
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

    agents_result = _install_agents_config(runtime, home_dir)
    if agents_result:
        result["agents_config"] = agents_result

    return result
