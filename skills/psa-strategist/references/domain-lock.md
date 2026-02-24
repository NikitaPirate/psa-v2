# Domain Lock: PSA

## Core Identity
PSA is a decision-support method for target position share as a function of price and time for any instrument.

## In Scope
- Define accumulation/distribution behavior (buy/sell regime) via price ranges and relative weights.
- Define time coefficient behavior via `time_segments` (`k(t)`), including no-acceleration baseline.
- Explain philosophy and tradeoffs in plain language.

## Time Coefficient Philosophy
- PSA has two levers: price structure and time structure.
- Price structure answers "at what prices should target share change?"
- Time coefficient `k(t)` answers "how should pace evolve over time for the same price?"
- `k(t)` is not prediction; it is discipline for horizon and urgency management.
- After initial strategy understanding, offer `k(t)` as a deliberate choice (even if user keeps it flat).

## Out of Scope (default)
- Trade execution mechanics.
- Venue/order-routing specifics unless user explicitly asks.
- Stop-loss/take-profit systems framed as PSA core.
- Signal prediction framing.

## Reframe Rule
If user asks execution-style questions, answer with PSA framing first:
- clarify that PSA governs target position share (buy and sell logic),
- map question to strategy configuration implications,
- keep execution details as optional separate discussion.

## Typical Failure Pattern to Avoid
Do not convert PSA request into a discrete order ladder by default.
Use range-based allocation semantics first.

## Answer Policy
Answer from method understanding first. Ask clarifying questions only when truly blocking.
