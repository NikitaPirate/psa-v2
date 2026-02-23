# Log Payload Guide

`psa log append` accepts any JSON object. Use stable event shapes so cross-session interpretation stays deterministic.

## Required Baseline Fields
For every event, prefer:
- `event_type`: short machine-friendly event name
- `summary`: one-line human summary
- `author`: `user` or `agent`

## Recommended Event Types
- `strategy_revision`: strategy changed and upserted
- `checkin`: evaluated market point(s) and recorded interpretation
- `decision`: user-level decision linked to current strategy
- `constraint_update`: risk/budget/behavior constraints changed

## Suggested Payload Shapes

`strategy_revision`:
```json
{
  "event_type": "strategy_revision",
  "summary": "Increased deep drawdown allocation",
  "author": "agent",
  "change": {
    "from_revision": 2,
    "to_revision": 3,
    "highlights": [
      "30k-40k segment weight: 35 -> 45",
      "time acceleration reduced"
    ]
  }
}
```

`checkin`:
```json
{
  "event_type": "checkin",
  "summary": "Point evaluation at 42k",
  "author": "agent",
  "observation": {
    "timestamp": "2026-03-01T00:00:00Z",
    "price": 42000
  },
  "result": {
    "target_share": 0.47,
    "base_share": 0.39
  }
}
```

`decision`:
```json
{
  "event_type": "decision",
  "summary": "User approved base variant",
  "author": "user",
  "decision": {
    "action": "save_revision",
    "reason": "balanced downside coverage"
  }
}
```

## Save Ordering Rule
When a strategy changes:
1. run `strategy upsert`,
2. then append `strategy_revision` log with returned revision.

If upsert fails, do not append revision log.
