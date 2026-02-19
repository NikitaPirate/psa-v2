# AGENTS.md

This file defines contributor rules for `psa-v2`.

## 1. How to read docs before changing code

Read in this order:
1. `docs/ARCHITECTURE.md`
2. `docs/DOMAIN_MODEL.md`
3. `docs/MATH_SPEC.md`
4. `docs/CONTRACTS.md`
5. `docs/TESTING_STRATEGY.md`
6. relevant ADR in `docs/adr/`

## 2. Source-of-truth ownership

- Architecture ownership: `docs/ARCHITECTURE.md`
- Domain type ownership: `docs/DOMAIN_MODEL.md`
- Math and invariant ownership: `docs/MATH_SPEC.md`
- Contract ownership: `docs/CONTRACTS.md`
- Test policy ownership: `docs/TESTING_STRATEGY.md`

Do not redefine normative rules outside the owner document.

## 3. Anti-duplication policy (strict)

- Normative text must exist in exactly one owner document.
- Repeating normative text from any existing documentation file is forbidden, including in `AGENTS.md`.
- Other docs must link to the owner section instead of repeating text.
- Copy-paste duplication of normative statements is forbidden.

## 4. Documentation update workflow

When a rule changes:
1. Update the owner document first.
2. Update any references that point to it.
3. Do not duplicate the updated rule in referencing docs.

## 5. Separation of concerns in docs

- Spec/intent docs: rules, formulas, contracts, invariants.
- Tutorial/example docs: usage examples and walkthroughs.

Do not mix tutorial prose into normative sections.

## 6. Rules for updating AGENTS.md

- Update only governance/process rules here.
- Do not restate architecture, math, or contract spec text.
- If AGENTS needs to mention a technical rule, link the owner doc instead of repeating it.
- Before commit, scan AGENTS for repeated normative sentences already present in other docs.

## 7. Code constraints

- Keep `core/src/psa_core` independent from framework-specific model libraries.
- Use absolute imports across project packages; avoid relative imports.
- Keep validation explicit and local to boundary adapters.
- Preserve deterministic behavior.

## 8. Changelog policy

- Do not update `CHANGELOG.md` during regular implementation iterations.
- Update `CHANGELOG.md` only in the final pre-PR pass.

## 9. UV workflow in this repo

- Use `uv sync` to prepare environment (do not add `--group dev`).
- Run tools via `uv run <tool>` (for example: `uv run pytest`, `uv run ruff check .`).
- Do not use `uv run --with ...` for regular project commands or hooks.

## 10. Release workflow docs

- Tag-driven release process for `psa-strategy-core` and `psa-strategy-cli` is documented in `docs/RELEASE_RUNBOOK.md`.
- Keep release process details in the runbook and link to it instead of duplicating instructions in other docs.
