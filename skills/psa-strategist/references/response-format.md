# Response Format Policy

## Default Output Shape
1. One-paragraph summary in plain language.
2. Comparison view in a readable layout (table/cards/ASCII block).
3. Action prompt in plain language (save/update/compare).

## Adaptive Rendering Ladder
Use the first readable option, then fallback as needed:
1. Compact Markdown table(s).
2. Split into two smaller tables (zone weights, then target share).
3. Monospaced ASCII table in fenced `text` block.
4. Card/list view by variant.

Trigger fallback when:
- user says "поехало", "разъехалось", "непонятно", "перерисуй";
- table would be too wide for the current client;
- columns become too dense for one table.

## Deterministic Rendering
- For multi-variant output with many columns, prefer `scripts/render_strategy_view.py`.
- Keep content semantics stable while changing layout.
- Never rerender in the same broken shape after user asks to redraw.

## JSON Handling
- Do not start with raw JSON.
- Provide JSON only on explicit request or in clearly marked technical appendix.
- Never make user parse JSON to proceed.

## Save Flow
When user says "save", save directly and confirm what was saved.
Do not ask user to copy/paste JSON unless user explicitly asks for manual mode.
