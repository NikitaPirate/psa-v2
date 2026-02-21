from __future__ import annotations

import json
from typing import Any


def _json_dumps(payload: dict[str, Any], *, pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=False) + "\n"
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=False) + "\n"


def render_success(result: Any, *, output_format: str, pretty: bool) -> str:
    envelope = {"ok": True, "result": result}
    if output_format == "json":
        return _json_dumps(envelope, pretty=pretty)

    if isinstance(result, str):
        return result.rstrip("\n") + "\n"

    return _json_dumps(envelope, pretty=True)


def render_error(*, code: str, message: str, pretty: bool) -> str:
    envelope = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    return _json_dumps(envelope, pretty=pretty)
