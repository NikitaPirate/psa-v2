#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _read_payload(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("input root must be an object")
    return data


def _coerce_percent(value: Any) -> str:
    if isinstance(value, (int, float)):
        if 0.0 <= float(value) <= 1.0:
            pct = float(value) * 100.0
        else:
            pct = float(value)
        if float(pct).is_integer():
            return f"{int(pct)}%"
        return f"{pct:.1f}".rstrip("0").rstrip(".") + "%"
    if isinstance(value, str):
        return value
    return "-"


def _sort_price_keys(keys: list[str]) -> list[str]:
    def _key_weight(k: str) -> tuple[int, str]:
        digits = ""
        for ch in k:
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        if digits:
            return (-int(digits), k)
        return (0, k)

    return sorted(keys, key=_key_weight)


def _collect_columns(variants: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    zone_keys: set[str] = set()
    target_keys: set[str] = set()
    for variant in variants:
        zones = variant.get("zone_weights", {})
        targets = variant.get("target_share", {})
        if isinstance(zones, dict):
            zone_keys.update(str(k) for k in zones.keys())
        if isinstance(targets, dict):
            target_keys.update(str(k) for k in targets.keys())
    return _sort_price_keys(list(zone_keys)), _sort_price_keys(list(target_keys))


def _build_md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines: list[str] = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _build_ascii_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def _fmt_row(cols: list[str]) -> str:
        return " | ".join(col.ljust(widths[idx]) for idx, col in enumerate(cols))

    sep = "-+-".join("-" * w for w in widths)
    out = [_fmt_row(headers), sep]
    out.extend(_fmt_row(row) for row in rows)
    return "\n".join(out)


def _render_cards(variants: list[dict[str, Any]], zone_keys: list[str], target_keys: list[str]) -> str:
    blocks: list[str] = []
    for variant in variants:
        label = str(variant.get("label", "Option"))
        zones = variant.get("zone_weights", {})
        targets = variant.get("target_share", {})

        zone_line = ", ".join(
            f"{k}: {zones.get(k, '-') if isinstance(zones, dict) else '-'}" for k in zone_keys
        )
        target_line = ", ".join(
            f"{k}: {_coerce_percent(targets.get(k, '-')) if isinstance(targets, dict) else '-'}"
            for k in target_keys
        )

        block = [
            f"{label}",
            f"- Budget by zones: {zone_line}" if zone_keys else "- Budget by zones: -",
            f"- Target share: {target_line}" if target_keys else "- Target share: -",
        ]

        for key, title in [
            ("thesis_fit", "Thesis fit"),
            ("risk_posture", "Risk posture"),
            ("tradeoff", "Tradeoff"),
        ]:
            value = variant.get(key)
            if isinstance(value, str) and value.strip():
                block.append(f"- {title}: {value.strip()}")

        blocks.append("\n".join(block))

    return "\n\n".join(blocks)


def _render_tables(
    variants: list[dict[str, Any]],
    zone_keys: list[str],
    target_keys: list[str],
    *,
    formatter: str,
) -> str:
    headers_zone = ["Variant"] + zone_keys
    rows_zone: list[list[str]] = []
    for variant in variants:
        zones = variant.get("zone_weights", {})
        row = [str(variant.get("label", "Option"))]
        for k in zone_keys:
            if isinstance(zones, dict):
                row.append(str(zones.get(k, "-")))
            else:
                row.append("-")
        rows_zone.append(row)

    headers_target = ["Variant"] + target_keys
    rows_target: list[list[str]] = []
    for variant in variants:
        targets = variant.get("target_share", {})
        row = [str(variant.get("label", "Option"))]
        for k in target_keys:
            if isinstance(targets, dict):
                row.append(_coerce_percent(targets.get(k, "-")))
            else:
                row.append("-")
        rows_target.append(row)

    table_builder = _build_md_table if formatter == "md" else _build_ascii_table

    parts: list[str] = []
    if zone_keys:
        parts.append("1) Budget by price zones (%)")
        parts.append(table_builder(headers_zone, rows_zone))
    if target_keys:
        if parts:
            parts.append("")
        parts.append("2) Target accumulated share")
        parts.append(table_builder(headers_target, rows_target))

    commentary: list[str] = []
    for variant in variants:
        label = str(variant.get("label", "Option"))
        tradeoff = variant.get("tradeoff")
        if isinstance(tradeoff, str) and tradeoff.strip():
            commentary.append(f"- {label}: {tradeoff.strip()}")
    if commentary:
        if parts:
            parts.append("")
        parts.append("Tradeoffs")
        parts.extend(commentary)

    return "\n".join(parts).strip()


def render_view(payload: dict[str, Any], *, mode: str, max_width: int) -> str:
    variants_raw = payload.get("variants")
    if not isinstance(variants_raw, list) or not variants_raw:
        raise ValueError("input requires non-empty 'variants' array")

    variants = [item for item in variants_raw if isinstance(item, dict)]
    if not variants:
        raise ValueError("all variants must be objects")

    zone_keys, target_keys = _collect_columns(variants)

    if mode == "cards":
        body = _render_cards(variants, zone_keys, target_keys)
    elif mode in {"md", "ascii"}:
        body = _render_tables(variants, zone_keys, target_keys, formatter=mode)
    else:
        probe = _render_tables(variants, zone_keys, target_keys, formatter="md")
        too_wide = any(len(line) > max_width for line in probe.splitlines())
        has_many_columns = (len(zone_keys) + len(target_keys)) >= 12
        body = (
            _render_cards(variants, zone_keys, target_keys)
            if too_wide or has_many_columns
            else probe
        )

    lines: list[str] = []
    title = payload.get("title")
    summary = payload.get("summary")
    if isinstance(title, str) and title.strip():
        lines.append(title.strip())
    if isinstance(summary, str) and summary.strip():
        lines.append(summary.strip())
    if lines:
        lines.append("")
    lines.append(body)
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render investor-readable PSA strategy comparisons with stable layout."
    )
    parser.add_argument("--input", required=True, help="JSON file path or '-' for stdin.")
    parser.add_argument(
        "--format",
        choices=["auto", "md", "ascii", "cards"],
        default="auto",
        help="Output render mode. 'auto' selects md or cards based on width.",
    )
    parser.add_argument("--max-width", type=int, default=110, help="Width threshold for auto mode.")
    args = parser.parse_args(argv)

    try:
        payload = _read_payload(args.input)
        sys.stdout.write(render_view(payload, mode=args.format, max_width=args.max_width))
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"render_strategy_view error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
