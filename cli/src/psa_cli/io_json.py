from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from psa_cli.errors import CliIoError


def read_json_input(input_path: str) -> Any:
    source_label = "stdin" if input_path == "-" else input_path
    try:
        if input_path == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(input_path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CliIoError(f"invalid UTF-8 input in {source_label}: {exc}") from exc
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise CliIoError(f"failed to read input from {source_label}: {reason}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliIoError(f"invalid JSON in {source_label}: {exc.msg}") from exc


def write_json_output(payload: Any, output_path: str, *, pretty: bool) -> None:
    if pretty:
        text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    else:
        text = json.dumps(payload, separators=(",", ":"), sort_keys=False) + "\n"

    target_label = "stdout" if output_path == "-" else output_path
    try:
        if output_path == "-":
            sys.stdout.write(text)
        else:
            Path(output_path).write_text(text, encoding="utf-8")
    except OSError as exc:
        raise CliIoError(
            f"failed to write output to {target_label}: {exc.strerror or str(exc)}"
        ) from exc
