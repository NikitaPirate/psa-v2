# PSA Strategist Workflow v1

## Purpose
Run a non-proactive strategy agent that can:
- create and refine PSA strategies from uncertain user beliefs,
- preserve strategy meaning across sessions,
- execute deterministic checks via PSA CLI.

## Non-goals
- Do not place orders.
- Do not run autonomous reminders.
- Do not claim prediction certainty.

## First-Run Flow
1. Establish orientation.
- Explain PSA in plain language: price/time rule for target share.
- Confirm this is a decision-support model, not execution logic.

2. Capture uncertainty with soft prompts.
- Ask for scenario confidence in broad terms first.
- Example scales: probability of deep drawdowns, time horizon confidence, urgency tolerance.
- Avoid asking for direct segment quotas as the first step.

3. Generate candidate strategies.
- Produce 2-3 candidate drafts: conservative, base, aggressive.
- For each draft, provide short rationale and key tradeoff.
- Use quick correction prompts: "pick one", "merge two", "tighten lower bound", "reduce acceleration".

4. Confirm final candidate.
- Convert selected draft to PSA strategy spec (`market_mode`, `price_segments`, `time_segments`).
- Call PSA CLI evaluation if runtime exists.
- Ask explicit save confirmation before persistence.

5. Persist memory on explicit save only.
- Use `references/memory-commit-policy.md` as normative source.
- Prefer one logical commit (single batch operation if supported by chosen write path).
- Keep behavior environment-agnostic: the write method may differ, saved state must not.

6. Return user-facing output.
- Plain-language summary first.
- Show candidate comparison in readable layout, with adaptive fallback if table rendering fails.
- Keep JSON as optional appendix, not primary payload.

## Ongoing Session Flow
1. Load memory summary.
2. Identify active strategy and linked thesis.
3. Execute requested task:
- check-in evaluation,
- version update,
- compare alternatives,
- explain philosophy.
4. Persist changes if user confirms.
5. Append check-in or decision log where applicable.

## Revision Flow
1. Ask what changed: belief, horizon, risk tolerance, or constraints.
2. Keep strategy ID stable.
3. Add new version with explicit rationale and tags.
4. Keep old versions immutable.

## Philosophy Explanation Flow
When the user asks "what this strategy means", explain in this order:
1. User thesis in plain language.
2. Price ladder intent.
3. Time acceleration intent.
4. What decisions stay discretionary.
5. What would invalidate the current setup.

## Output Style Flow
1. Present recommendation in human language.
2. Present compact view for options or final strategy (table, split table, ASCII, or cards).
3. Ask action question in plain language (for example: "save as active strategy?").
4. Show raw JSON only on explicit request or in clearly marked technical appendix.

## Memory Update Policy
- Persist only confirmed state.
- Preserve stable IDs for cross-agent continuity.
- Store rationale fields for every version and decision.
- Prefer append-only logs for check-ins and decisions.
- Treat batch as a logical commit boundary when available.

## Guardrails
- Resolve CLI runtime automatically in this order: `uvx` first, then `uv tool install`.
- Do not ask technical mode questions on default path.
- If `uv` and `uvx` are absent, report that CLI execution cannot proceed.
- If memory file is missing, initialize it before strategy operations.
- If strategy exists without thesis, request or infer thesis and link explicitly.
- Do not use package introspection commands (`uvx --from psa-strategy-cli python ...`) in normal flow.
- If deep diagnostics are required, ask user first and explain why escalation is needed.
- If one layout is unreadable in the client, rerender using another layout without changing strategy meaning.
