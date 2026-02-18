# Math Spec

## Definitions

- `S_base(p, mode)` - normalized share from price only, in `[0, 1]`.
- `k(t)` - time coefficient from piecewise-linear time segments.
- `p_virtual` - transformed price used for time-adjusted target.
- `S_target` - target share at transformed price.

## Price share

For each non-overlapping segment with normalized weight `w_i`:

- `mode = bear`:
  - share rises as price moves lower.
- `mode = bull`:
  - share rises as price moves higher.

Total price share is weighted sum across segments and clamped to `[0, 1]`.

## Time coefficient

`k(t)` behavior:
- before first segment start: first `k_start`,
- inside segment: linear interpolation from `k_start` to `k_end`,
- in gaps: previous segment `k_end`,
- after last segment end: last `k_end`.

## Virtual price transform

- `bear`: `p_virtual = p / k(t)`
- `bull`: `p_virtual = p * k(t)`

With non-decreasing `k(t)`, both modes become more advanced in target share over time.

## Numerical stability guard

- Computation may use a small `EPS` constant only as a numeric guard in formulas.
- `EPS` is allowed for division/interpolation safety in math routines.
- Domain constraints are validated with strict inequalities and are not relaxed by `EPS`.
- Example: `weight >= 0` and `sum(weight) > 0` are validation rules, not numerical heuristics.

## Invariants

- `0 <= S_base <= 1`
- `0 <= S_target <= 1`
- For fixed time:
  - bear mode: lower price must not reduce share,
  - bull mode: higher price must not reduce share.
- For fixed price and non-decreasing `k(t)`: target share must not decrease over time.
