# ADR 0005: Single Compute Core and Portable Strategy Payload

## Status
Accepted

## Context
The platform has multiple interaction surfaces (agent, CLI, web, API), but strategy semantics must remain consistent.
Duplicating computation logic across surfaces would create drift risk and increase maintenance cost.
Cross-surface workflows also require a stable transfer unit for strategy data.

## Decision
- Keep Python core as the single computation source of truth.
- Expose core semantics through boundary adapters (CLI/API) instead of re-implementing math in clients.
- Use one canonical transferable strategy payload shape across surfaces.
- Keep strategy transfer format as plain JSON payload content (text or `.json` file), without mandatory bridge schema.

Normative rule locations:
- architecture ownership: `docs/ARCHITECTURE.md`
- contract ownership: `docs/CONTRACTS.md`

## Consequences
- Cross-surface behavior remains deterministic under shared core semantics.
- UI and agent layers can evolve independently from math implementation details.
- Transfer workflows stay simple and tool-agnostic through canonical JSON payload portability.
