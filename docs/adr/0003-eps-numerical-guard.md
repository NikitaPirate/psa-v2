# ADR 0003: EPS as Numerical Guard Only

## Status
Accepted

## Context
The core uses floating-point arithmetic for piecewise interpolation and virtual-price transforms.
Without a numeric guard, edge cases near zero can create unstable division behavior.

## Decision
Use `EPS` only in computation routines as a numeric safety guard.

Normative rule location:
- `docs/MATH_SPEC.md` -> section `Numerical stability guard`.

## Consequences
- Stable behavior on near-zero numeric edges.
- Clear separation between numeric guards and domain validation rules.
- Domain constraints remain strict and explicit (`weight >= 0`, total weight `> 0`).
