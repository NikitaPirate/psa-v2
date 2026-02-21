# psa-strategy-cli

CLI package for PSA strategy workflows.

Package/install name: `psa-strategy-cli`  
Command name: `psa`

## Installation

```bash
uv tool install psa-strategy-cli
psa --version
```

If `psa` is not found after install, run:

```bash
uv tool update-shell
```

## Output contract

Global flags:

- `--format json|text` (default: `json`)
- `--pretty`

Success envelope (`json` mode):

```json
{"ok": true, "result": {...}}
```

Error envelope (always JSON, written to stderr):

```json
{"ok": false, "error": {"code": "...", "message": "..."}}
```

Exit codes:

- `0`: success
- `2`: arguments
- `3`: runtime
- `4`: validation
- `5`: state/not-found/conflict
- `1`: internal

## Memory model

CLI keeps strategy memory in `psa-memory.v1` format. Default storage is:

- `<cwd>/.psa/psa-memory.v1.json`

For tests/debug you can override path with hidden flag `--db-path`.

## Commands

### Show

- `psa show runtime`
- `psa show memory --view summary|full`
- `psa show strategy --id <strategy_id> --include versions --include theses --include checkins --include decisions`
- `psa show thesis --id <thesis_id>`
- `psa show checkins --strategy-id <strategy_id> --limit <n>`
- `psa show decisions --strategy-id <strategy_id> --limit <n>`

### Upsert

- `psa upsert thesis ...`
- `psa upsert strategy ... [--set-active]`
- `psa upsert profile ...`
- `psa upsert version ...`
- `psa upsert link --strategy-id ... --thesis-id ...`
- `psa upsert checkin ...` (idempotent by `--id`; fails on legacy duplicate ids)
- `psa upsert decision ...` (idempotent by `--id`; fails on legacy duplicate ids)
- `psa upsert strategy-state --json '<payload>'`

### Evaluate

- default flow (latest strategy version):
  - `psa evaluate point --timestamp ... --price ...`
  - `psa evaluate rows --row <timestamp:price> --row <timestamp:price>`
  - `psa evaluate ranges --price-start ... --price-end ... --price-steps ... --time-start ... --time-end ... --time-steps ... [--include-price-breakpoints]`
- optional explicit sources:
  - `--version-id <id>`
  - `--strategy-id <id>` (use latest version of selected strategy)
- inline draft mode:
  - `psa evaluate point|rows|ranges --market-mode ... --price-segment <low:high:weight> [--price-segment ...] [--time-segment <start:end:k_start:k_end>]`
- source flags are mutually exclusive:
  - `--version-id` cannot be combined with `--strategy-id` or inline flags
  - `--strategy-id` cannot be combined with inline flags

## Examples

### Runtime and empty memory

```bash
psa show runtime
psa show memory --view summary
```

### First save in one command

```bash
psa upsert strategy-state --json '{
  "thesis": {
    "id": "thesis-1",
    "title": "Weak market accumulation",
    "summary": "Base thesis",
    "assumptions": ["cycle persists"],
    "invalidation_signals": ["structural break"],
    "horizon": "2026-12-31",
    "status": "active"
  },
  "strategy": {
    "id": "strategy-1",
    "name": "Base bear strategy",
    "objective": "Accumulate with discipline",
    "market_mode": "bear",
    "notes": "initial",
    "status": "active"
  },
  "version": {
    "id": "version-1",
    "label": "v1",
    "rationale": "initial",
    "created_by": "agent",
    "strategy_spec": {
      "market_mode": "bear",
      "price_segments": [
        {"price_low": 50000, "price_high": 60000, "weight": 10},
        {"price_low": 40000, "price_high": 50000, "weight": 30}
      ],
      "time_segments": []
    }
  },
  "link": {"rationale": "thesis drives strategy"},
  "set_active": true
}'
```

### Revision save in one command

```bash
psa upsert strategy-state --json '{
  "version": {
    "id": "version-2",
    "strategy_id": "strategy-1",
    "label": "v2",
    "rationale": "higher acceleration",
    "created_by": "agent",
    "strategy_spec": {
      "market_mode": "bear",
      "price_segments": [
        {"price_low": 50000, "price_high": 60000, "weight": 10},
        {"price_low": 40000, "price_high": 50000, "weight": 30}
      ],
      "time_segments": [
        {
          "start_ts": "2026-01-01T00:00:00Z",
          "end_ts": "2026-06-01T00:00:00Z",
          "k_start": 1.0,
          "k_end": 1.8
        }
      ]
    }
  },
  "set_active": true
}'
```

### Evaluate by latest version (default)

```bash
psa evaluate point \
  --timestamp 2026-03-01T00:00:00Z \
  --price 42000
```

### Evaluate with explicit version override

```bash
psa evaluate point \
  --version-id version-1 \
  --timestamp 2026-03-01T00:00:00Z \
  --price 42000
```
