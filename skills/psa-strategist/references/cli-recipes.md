# CLI Recipes (PSA-only)

## Runtime Bootstrap
1. Check command:
```bash
psa --version
```
2. If missing:
```bash
uv tool install psa-strategy-cli
psa --version
```
3. If still missing:
```bash
uv tool update-shell
```

## Normal-Flow Restriction
- Use `psa` as the only operational interface.
- Do not use `uvx` in normal flow.
- Do not use `uv run python` helper scripts.
- Do not require user-managed input/output JSON files for normal flow.

## Read State
```bash
psa show runtime
psa show memory --view summary
psa show strategy --id strategy-1 --include versions --include theses
```

## Atomic First Save
```bash
psa create strategy-pack --json '{
  "thesis": {"id": "thesis-1", "title": "Weak market accumulation"},
  "strategy": {
    "id": "strategy-1",
    "name": "Base bear strategy",
    "market_mode": "bear"
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

## Atomic Revision Save
```bash
psa update strategy-pack --json '{
  "strategy": {"id": "strategy-1", "notes": "revision"},
  "version": {
    "id": "version-2",
    "strategy_id": "strategy-1",
    "label": "v2",
    "rationale": "increase acceleration",
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
  "set_active": true
}'
```

## Evaluate by Version
```bash
psa evaluate point --version-id version-1 --timestamp 2026-03-01T00:00:00Z --price 42000
psa evaluate rows --version-id version-1 --row 2026-02-01T00:00:00Z:47000 --row 2026-03-01T00:00:00Z:44000
```

## Evaluate Inline Draft
```bash
psa evaluate point \
  --market-mode bear \
  --price-segment 50000:60000:10 \
  --price-segment 40000:50000:30 \
  --price-segment 30000:40000:40 \
  --price-segment 25000:30000:20 \
  --timestamp 2026-03-01T00:00:00Z \
  --price 42000
```

## Missing Runtime Message Template
Use this exact meaning:
- "PSA CLI cannot run in this environment because `uv` or PATH configuration is missing. Install/configure `uv`, then I can continue with evaluations."
