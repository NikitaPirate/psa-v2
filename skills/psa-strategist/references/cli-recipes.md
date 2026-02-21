# CLI Recipes (strategy + log)

Command permissions and bootstrap policy are defined in `references/command-authority.md`.

## Runtime Bootstrap
```bash
psa --version
uv tool install psa-strategy-cli
psa --version
uv tool update-shell
```

## Read State
```bash
psa strategy list --json
psa strategy show --strategy-id main --json
psa log tail --strategy-id main --limit 20 --json
```

## Mutations (canonical forms)
```bash
psa strategy upsert --strategy-id main --input - --json
psa log append --strategy-id main --input - --json
```

`strategy upsert` stdin shape:
```json
{"market_mode":"bear","price_segments":[{"price_low":50000,"price_high":60000,"weight":10}],"time_segments":[]}
```

`log append` stdin shape:
```json
{"event_type":"strategy_revision","summary":"Adjusted downside allocation","author":"agent"}
```

## Evaluate by Persisted Strategy (canonical forms)
```bash
psa evaluate-point --strategy-id main --input - --output - --json
psa evaluate-rows --strategy-id main --input - --output - --json
psa evaluate-ranges --strategy-id main --input - --output - --json
```

`evaluate-point` stdin shape:
```json
{"timestamp":"2026-03-01T00:00:00Z","price":42000}
```

`evaluate-rows` stdin shape:
```json
{"rows":[{"timestamp":"2026-02-01T00:00:00Z","price":47000},{"timestamp":"2026-03-01T00:00:00Z","price":44000}]}
```

`evaluate-ranges` stdin shape:
```json
{"price_start":60000,"price_end":25000,"price_steps":4,"time_start":"2026-02-01T00:00:00Z","time_end":"2026-04-01T00:00:00Z","time_steps":3,"include_price_breakpoints":true}
```

## Missing Runtime Message Template
Use this exact meaning:
- "PSA CLI cannot run in this environment because `uv` or PATH configuration is missing. Install/configure `uv`, then I can continue with evaluations."
