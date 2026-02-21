# PSA Strategist Workflow v2 (CLI-only)

## Purpose
Run a non-proactive strategy agent that:
- creates and refines PSA strategies from uncertain assumptions,
- preserves strategy meaning across sessions,
- executes checks through PSA CLI only.

## Non-goals
- Do not place orders.
- Do not run autonomous reminders.
- Do not claim prediction certainty.

## First-Run Flow
1. Establish orientation.
- Explain PSA in plain language: target share as a function of price and time.
- Confirm this is decision-support, not execution logic.

2. Capture uncertainty with soft prompts.
- Ask for broad scenario confidence and horizon.
- Avoid starting from rigid parameter forms.

3. Generate candidates.
- Produce up to 3 drafts: conservative/base/aggressive.
- Provide one-line thesis fit and one-line tradeoff for each.

4. Validate candidate.
- Convert chosen draft into PSA spec.
- Run deterministic CLI evaluation with `psa evaluate ...`.

5. Confirm save explicitly.
- Ask direct confirmation (`save`, `сохраняй`, `фиксируй`).

6. Persist in one logical command.
- Save via: `psa upsert strategy-state --json '<payload>'`.

7. Return output.
- Human summary first.
- Readable comparison or final view.
- JSON only on explicit request or appendix.

## Ongoing Session Flow
1. Read memory summary with `psa show memory --view summary`.
2. Resolve active strategy and linked thesis.
3. Execute requested task (`evaluate`, `upsert`, `show`, explain).
4. Persist only on explicit confirmation.
5. Append check-in or decision when relevant.

## Revision Flow
1. Ask what changed: belief, horizon, risk posture, constraints.
2. Keep strategy ID stable.
3. Add a new version with rationale.
4. Keep prior versions immutable.

## Evaluate Flow Default
- Default source is latest strategy version (active strategy).
- `--version-id` is optional override for explicit historical checks.

## Guardrails
- Runtime bootstrap is tool-install only: `uv tool install psa-strategy-cli`.
- No `uvx` in normal flow.
- No helper Python scripts in normal flow.
- No file-path workflow assumptions for agent actions.
- If runtime is blocked (`uv`/PATH), report blocker clearly and stop execution.
