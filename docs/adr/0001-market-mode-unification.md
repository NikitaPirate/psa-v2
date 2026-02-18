# ADR 0001: Market Mode Unification

## Status
Accepted

## Context
Earlier direction modeling can be represented with multiple overlapping fields.
That adds inconsistent combinations and validation complexity.

## Decision
Use one field only:
- `market_mode = bear | bull`

Semantic lock:
- `bear` maps to accumulation behavior.
- `bull` maps to distribution behavior.

## Consequences
- Fewer invalid state combinations.
- Smaller public contract surface.
- Simpler test matrix.
