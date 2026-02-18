# ADR 0002: No Pydantic in Core

## Status
Accepted

## Context
The project goal is a minimal, portable computation core with explicit behavior.

## Decision
- Core runtime uses stdlib dataclasses and explicit validation functions.
- JSON Schema files are maintained as contract artifacts.
- `jsonschema` is used in tests/dev only.

## Consequences
- No framework lock-in in domain logic.
- Slightly more manual boundary code.
- Contracts stay language-agnostic.
