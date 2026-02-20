# PSA JSON Templates (v1)

Use these templates when local `examples/*.json` are unavailable.
Use only public CLI contracts; avoid package introspection.

## StrategySpec Template

```json
{
  "market_mode": "bear",
  "price_segments": [
    {"price_low": 50000, "price_high": 60000, "weight": 10},
    {"price_low": 40000, "price_high": 50000, "weight": 30},
    {"price_low": 30000, "price_high": 40000, "weight": 40},
    {"price_low": 25000, "price_high": 30000, "weight": 20}
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
```

Notes:
- `market_mode`: `bear` or `bull`
- At least one `weight > 0`
- `time_segments` may be empty array

## evaluate-point Request

```json
{
  "strategy": {
    "market_mode": "bear",
    "price_segments": [
      {"price_low": 50000, "price_high": 60000, "weight": 10},
      {"price_low": 40000, "price_high": 50000, "weight": 30},
      {"price_low": 30000, "price_high": 40000, "weight": 40},
      {"price_low": 25000, "price_high": 30000, "weight": 20}
    ],
    "time_segments": [
      {
        "start_ts": "2026-01-01T00:00:00Z",
        "end_ts": "2026-06-01T00:00:00Z",
        "k_start": 1.0,
        "k_end": 1.8
      }
    ]
  },
  "timestamp": "2026-03-01T00:00:00Z",
  "price": 42000
}
```

## evaluate-rows Request

```json
{
  "strategy": {
    "market_mode": "bear",
    "price_segments": [
      {"price_low": 50000, "price_high": 60000, "weight": 10},
      {"price_low": 40000, "price_high": 50000, "weight": 30},
      {"price_low": 30000, "price_high": 40000, "weight": 40},
      {"price_low": 25000, "price_high": 30000, "weight": 20}
    ],
    "time_segments": [
      {
        "start_ts": "2026-01-01T00:00:00Z",
        "end_ts": "2026-06-01T00:00:00Z",
        "k_start": 1.0,
        "k_end": 1.8
      }
    ]
  },
  "rows": [
    {"timestamp": "2026-02-01T00:00:00Z", "price": 47000},
    {"timestamp": "2026-03-01T00:00:00Z", "price": 44000},
    {"timestamp": "2026-04-01T00:00:00Z", "price": 41000}
  ]
}
```

## evaluate-ranges Request

```json
{
  "strategy": {
    "market_mode": "bear",
    "price_segments": [
      {"price_low": 50000, "price_high": 60000, "weight": 10},
      {"price_low": 40000, "price_high": 50000, "weight": 30},
      {"price_low": 30000, "price_high": 40000, "weight": 40},
      {"price_low": 25000, "price_high": 30000, "weight": 20}
    ],
    "time_segments": [
      {
        "start_ts": "2026-01-01T00:00:00Z",
        "end_ts": "2026-06-01T00:00:00Z",
        "k_start": 1.0,
        "k_end": 1.8
      }
    ]
  },
  "price_start": 60000,
  "price_end": 25000,
  "price_steps": 4,
  "time_start": "2026-02-01T00:00:00Z",
  "time_end": "2026-04-01T00:00:00Z",
  "time_steps": 3,
  "include_price_breakpoints": true
}
```

## Response Shapes

`evaluate-point`:
```json
{"row": {"timestamp": "...", "price": 0, "time_k": 0, "virtual_price": 0, "base_share": 0, "target_share": 0}}
```

`evaluate-rows` and `evaluate-ranges`:
```json
{"rows": [{"timestamp": "...", "price": 0, "time_k": 0, "virtual_price": 0, "base_share": 0, "target_share": 0}]}
```
