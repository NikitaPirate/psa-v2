# psa-strategy-cli

Command-line interface for PSA strategy evaluation contracts.

Package/install name: `psa-strategy-cli`  
Command name: `psa`

## Quick start (published package)

Run without installing:

```bash
uvx --from psa-strategy-cli psa --version
```

Install as a tool:

```bash
uv tool install psa-strategy-cli
psa --version
```

## Workspace development mode

Run commands from the `cli/` directory:

```bash
cd cli
```

## Commands

- `psa evaluate-point --input <path|-> --output <path|-> [--pretty]`
- `psa evaluate-rows --input <path|-> --output <path|-> [--pretty]`
- `psa evaluate-ranges --input <path|-> --output <path|-> [--pretty]`
- `psa --version`

`-` means standard stream (`stdin` for `--input`, `stdout` for `--output`).

## Input and output

- Input must be a JSON request matching the command request schema.
- Output is JSON response (`{"row": ...}` or `{"rows": [...]}`).
- By default, output JSON is compact.
- `--pretty` enables indented output.

## Examples

### Evaluate point from file to stdout

```bash
uv run --package psa-strategy-cli psa evaluate-point \
  --input ../examples/bear_accumulate_point.json \
  --output -
```

### Evaluate rows with pretty output file

```bash
uv run --package psa-strategy-cli psa evaluate-rows \
  --input ../examples/batch_timeseries_rows.json \
  --output /tmp/rows.json \
  --pretty
```

### Evaluate ranges with stdin/stdout

```bash
cat ../examples/range_timeseries_rows.json | \
uv run --package psa-strategy-cli psa evaluate-ranges --input - --output -
```

## Exit codes

- `0`: success
- `2`: CLI argument error
- `3`: I/O or JSON parsing error
- `4`: schema/contract/runtime validation error
- `1`: unexpected internal error

## Schema loading

CLI searches request schemas in this order:

1. `PSA_SCHEMA_DIR` (if set)
2. packaged schemas bundled inside the installed `psa-strategy-cli` distribution
3. repository `schemas/` directory (development fallback)
