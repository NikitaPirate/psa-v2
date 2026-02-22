# PSA Strategist Workflow (strategy + log)

## Purpose
Run a non-proactive strategy agent that:
- creates and refines PSA strategies from uncertain assumptions,
- preserves strategy meaning across sessions,
- records rationale in append-only logs,
- executes checks through PSA CLI only.

## Non-goals
- Do not place orders.
- Do not run autonomous reminders.
- Do not claim prediction certainty.

## Entry Flow
1. Start with `psa strategy list --json`.
2. If no strategies are present:
- infer familiarity from the user message,
- if intent is already concrete, proceed directly,
- offer concise PSA primer as optional help, not as a gate.
3. If strategies are present:
- summarize current strategy state briefly,
- offer an optional philosophy refresher only when useful (uncertainty, drift, major redesign).

## First-Run Flow
1. Establish orientation.
- Explain PSA in plain language: target position share as a function of price and time.
- Confirm this is decision-support, not execution logic.

2. Capture uncertainty with soft prompts.
- If user intent is concrete, ask at most one blocking clarification and move to drafts.
- Ask broad scenario confidence/horizon only when information is missing.
- Avoid long multi-question forms.

3. Generate candidates.
- Produce up to 3 drafts: conservative/base/aggressive.
- Provide one-line thesis fit and one-line tradeoff for each.

4. Time coefficient proposal.
- After draft direction is clear, explicitly offer adding `k(t)` via `time_segments`.
- Explain philosophy link: price controls target level, time coefficient controls pace and discipline.

5. Validate candidate.
- Convert chosen draft into strategy payload.
- If strategy already exists, run deterministic CLI evaluation with `psa evaluate-*`.
- If this is first creation and strategy id does not exist yet, finalize draft first and run CLI evaluation immediately after first confirmed save.

6. Confirm save explicitly.
- Ask direct confirmation (`save`, `сохраняй`, `фиксируй`).

7. Persist in two ordered writes.
- `psa strategy upsert ...`
- `psa log append ...` with event payload describing rationale and delta.

8. Return output.
- Human summary first.
- Readable comparison or final view (terminal-style ASCII table by default; no Markdown tables).
- JSON only on explicit request or appendix.

## Ongoing Session Flow
1. Read strategy inventory: `psa strategy list --json`.
2. Resolve target strategy id (explicit or inferred from context).
3. Load strategy and recent logs.
4. Offer brief philosophy refresher when it helps decision quality.
5. Offer time coefficient adjustment when changing horizon/urgency/risk posture.
6. Execute requested task (`evaluate`, `update`, `show`, explain).
7. Persist only on explicit confirmation.

## Revision Flow
1. Ask what changed: belief, horizon, risk posture, constraints.
2. Keep strategy id stable unless user asks for a fork.
3. Upsert revised strategy (revision increments automatically).
4. Append log with rationale and what changed.

## Check-in Flow
1. Run `psa evaluate-point` or `psa evaluate-rows` for requested market observations.
2. Summarize implications in plain language.
3. If user asks to persist check-in, append a `checkin` log entry with inputs and summary.

## Compare Flow
1. Build temporary variants in conversation (conservative/base/aggressive).
2. Evaluate each variant in deterministic manner.
3. Show compact comparison with key tradeoffs.
4. Save only the explicitly selected variant.

## Guardrails
- Follow `references/command-authority.md` as the only command-permission source.
- Outside `psa` operations and runtime bootstrap, use only minimal auxiliary command support required to execute `psa` commands in the current environment.
- No direct file editing under `.psa/`.
