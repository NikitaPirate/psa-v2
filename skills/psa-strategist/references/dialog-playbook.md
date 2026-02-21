# Dialog Playbook

## Style Goals
- Keep conversation soft and adaptive.
- Replace rigid questionnaires with guided choices.
- Ask one compact block, then propose candidates.

## Recommended Opening Patterns
- "I can draft 3 strategy options from your assumptions, then we tune one."
- "If you are unsure about levels, give me scenario confidence and horizon first."
- "If you already have levels, I can convert them into a budget-managed PSA strategy."

## Soft Elicitation Blocks

### Block A: Scenario Confidence
Ask for 0-10 confidence on scenario depth examples. Keep ranges broad.
- mild drawdown
- medium drawdown
- deep drawdown

### Block B: Horizon and Urgency
Ask for target horizon and urgency tolerance.
- "How costly is waiting too long vs buying too early?"

### Block C: Existing User Artifacts
Ask whether user already has:
- pre-marked levels,
- prior strategy JSON,
- portfolio constraints.

## Candidate Presentation Template
For each candidate include:
- one-line thesis fit,
- one-line risk posture,
- one-line acceleration posture,
- key parameter differences.

Render as user-readable table/cards by default. Do not start with JSON.

Keep to 3 candidates max:
- conservative,
- base,
- aggressive.

## Correction Prompts
Use short correction commands:
- "Increase downside emphasis"
- "Reduce time pressure"
- "Move lower bound up/down"
- "Keep structure, change horizon"

## Finalization Prompt
Before persistence ask one explicit confirmation:
- "Should I save this as a new strategy version and mark it active?"

## Raw JSON Policy
- Offer JSON only as optional technical appendix.
- If user asks "save", perform save flow directly; do not require user to manually edit raw JSON.
