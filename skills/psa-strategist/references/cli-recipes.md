# CLI Recipes

## Preferred Runtime (auto)
Default strategy for the agent:
1. Try `uvx` first (no global install).
2. Fallback to `uv tool install` if `uvx` is unavailable.
3. If neither `uvx` nor `uv` exists, report a blocking setup issue.

Normal-flow restriction:
- Do not run package introspection commands like `uvx --from psa-strategy-cli python ...`.
- If diagnostics beyond public CLI are needed, ask for explicit user approval first.

## uvx Mode (ephemeral, first choice)
```bash
uvx --from psa-strategy-cli psa --version
```

Point request:
```bash
uvx --from psa-strategy-cli psa evaluate-point --input examples/bear_accumulate_point.json --output -
```

Rows request:
```bash
uvx --from psa-strategy-cli psa evaluate-rows --input examples/batch_timeseries_rows.json --output -
```

Ranges request:
```bash
uvx --from psa-strategy-cli psa evaluate-ranges --input examples/range_timeseries_rows.json --output -
```

## uv Tool Mode (persistent fallback)
```bash
uv tool install psa-strategy-cli
psa --version
```

Rows request:
```bash
psa evaluate-rows --input examples/batch_timeseries_rows.json --output -
```

Ranges request:
```bash
psa evaluate-ranges --input examples/range_timeseries_rows.json --output -
```

## Missing uv/uvx Message Template
Use this exact meaning:
- "PSA CLI cannot run in this environment because `uv`/`uvx` is missing. Install `uv` first, then I can continue with evaluations."
