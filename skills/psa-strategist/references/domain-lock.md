# Domain Lock: PSA

## Core Identity
PSA is a decision-support method for target BTC share as a function of price and time.

## In Scope
- Define accumulation behavior via price ranges and relative weights.
- Optionally define time acceleration via `time_segments`.
- Explain philosophy and tradeoffs in plain language.

## Out of Scope (default)
- Trade execution mechanics.
- Instrument selection debates (spot/perp) unless user explicitly insists.
- Stop-loss/take-profit systems framed as PSA core.
- Signal prediction framing.

## Reframe Rule
If user asks execution-style questions, answer with PSA framing first:
- clarify that PSA governs target share,
- map question to strategy configuration implications,
- keep execution details as optional separate discussion.

## Typical Failure Pattern to Avoid
Do not convert PSA request into discrete order ladder by default.
Use range-based allocation semantics first.

## Answer Policy
Answer from method understanding first. Ask clarifying questions only when truly blocking.
