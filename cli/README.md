# psa-strategy-cli

AI-first command-line interface for PSA strategy storage, logs, and evaluation.

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

## Storage model

The CLI persists state inside the current working directory:

- `.psa/strategies/<strategy_id>/strategy.json`
- `.psa/strategies/<strategy_id>/log.ndjson`

Directories are created automatically on first write.

## JSON mode

All operational commands require `--json`.

- Success: JSON payload in output stream.
- Error: JSON payload in `stderr` with:
  - `error.code`
  - `error.message`
  - `error.details`

## Commands

### Strategy

- `psa strategy upsert --strategy-id <id> --input <path|-> --json`
- `psa strategy list --json`
- `psa strategy show --strategy-id <id> --json`
- `psa strategy exists --strategy-id <id> --json`

### Log

- `psa log append --strategy-id <id> --input <path|-> --json`
- `psa log list --strategy-id <id> [--limit <n>] [--from-ts <ts>] [--to-ts <ts>] --json`
- `psa log show --strategy-id <id> --log-id <id> --json`
- `psa log tail --strategy-id <id> --limit <n> --json`

### Evaluate (strategy loaded from storage)

- `psa evaluate-point --strategy-id <id> --input <path|-> --output <path|-> --json [--pretty]`
- `psa evaluate-rows --strategy-id <id> --input <path|-> --output <path|-> --json [--pretty]`
- `psa evaluate-ranges --strategy-id <id> --input <path|-> --output <path|-> --json [--pretty]`

### Skill install

- `psa install-skill <runtime> [--skills-dir /path/to/skills-dir] [--agents-dir /path/to/agents-dir] --json`
- unknown runtime fallback: `psa install-skill any-runtime --skills-dir /path/to/skills-dir --json`

`-` means standard stream (`stdin` for `--input`, `stdout` for `--output`).

## Examples

### Create strategy

```bash
cat strategy.json | uv run --package psa-strategy-cli psa strategy upsert \
  --strategy-id main --input - --json
```

### Append log entry

```bash
echo '{"event":"thesis_updated","note":"reduced risk"}' | \
uv run --package psa-strategy-cli psa log append \
  --strategy-id main --input - --json
```

### Evaluate point using persisted strategy

```bash
echo '{"timestamp":"2026-01-01T00:00:00Z","price":45000}' | \
uv run --package psa-strategy-cli psa evaluate-point \
  --strategy-id main --input - --output - --json
```

## Exit codes

- `0`: success
- `2`: CLI argument error
- `3`: I/O or JSON parsing error
- `4`: validation/domain/storage error
- `1`: unexpected internal error

## Schema loading

CLI searches request schemas in this order:

1. `PSA_SCHEMA_DIR` (if set)
2. packaged schemas bundled inside the installed `psa-strategy-cli` distribution
3. repository `schemas/` directory (development fallback)
