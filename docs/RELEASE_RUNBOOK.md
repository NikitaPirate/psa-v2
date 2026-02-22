# Release Runbook (`psa-strategy-core` and `psa-strategy-cli`)

This runbook defines component-based releases in `psa-v2`.

## Scope

- `psa-strategy-core` and `psa-strategy-cli` are released independently from one repository.
- Release trigger is component tag, not a shared lockstep tag.
- Legacy lockstep tag `vX.Y.Z` is deprecated and blocked by CI.

## Release tag contract

- Core release tag: `core-vX.Y.Z`
- CLI release tag: `cli-vX.Y.Z`

`X.Y.Z` must match `[project].version` of the released package.

## Dependency policy (`cli -> core`)

- Exact pin is forbidden.
- CLI must depend on `psa-strategy-core` via compatibility range with one lower and one upper bound:
  - lower bound: `>=...`
  - upper bound: `<...`
- Upper bound policy:
  - if lower bound major is `>=1`: upper bound must be `<(major+1).0`
  - if lower bound major is `0`: upper bound must be `<0.(minor+1)`

Examples:
- `psa-strategy-core>=1.4,<2.0`
- `psa-strategy-core>=0.3,<0.4`

## One-time setup

1. Configure PyPI projects:
   - `psa-strategy-core`
   - `psa-strategy-cli`
2. Configure trusted publishing for both projects from this repository/workflows.
3. Configure GitHub Environment `pypi` with required reviewers.
4. Keep branch protection so CI must pass before merge.

## Versioning policy matrix

### Core (`psa-strategy-core`)

- MAJOR: backward-incompatible changes in public Python API, contracts, or semantics.
- MINOR: backward-compatible features.
- PATCH: backward-compatible fixes.

### CLI (`psa-strategy-cli`)

- MAJOR: backward-incompatible changes in CLI command/JSON contract.
- MINOR: backward-compatible command/features additions.
- PATCH: backward-compatible fixes.

### When CLI must raise core lower bound

Raise CLI lower bound when CLI starts relying on core behavior unavailable below that version.

## Validator

Use component validator before tagging and in CI:

```bash
uv run --no-project python scripts/release/verify_component_release.py --tag core-vX.Y.Z
uv run --no-project python scripts/release/verify_component_release.py --tag cli-vX.Y.Z
```

## Pre-tag validation

Run from repository root:

```bash
uv sync
uv run ruff check .
uv run pytest
uv build --package psa-strategy-core --out-dir dist/core
uv build --package psa-strategy-cli --out-dir dist/cli
uvx --from dist/cli/*.whl --with dist/core/*.whl psa --version
uvx --from dist/cli/*.whl --with dist/core/*.whl psa strategy upsert \
  --strategy-id smoke \
  --input examples/strategy_bear.json \
  --json
uvx --from dist/cli/*.whl --with dist/core/*.whl psa evaluate-point \
  --strategy-id smoke \
  --input examples/evaluate_point_input.json \
  --output - \
  --json
```

## Core release checklist

1. Update `/core/pyproject.toml` version.
2. Run validator:
   - `uv run --no-project python scripts/release/verify_component_release.py --tag core-vX.Y.Z`
3. Merge into `main`.
4. Create and push tag:

```bash
git tag core-vX.Y.Z
git push origin core-vX.Y.Z
```

5. Approve `pypi` environment when prompted.
6. Verify package visibility on PyPI.

## CLI release checklist

1. Update `/cli/pyproject.toml` version.
2. Ensure `psa-strategy-core` dependency range matches policy.
3. Run validator:
   - `uv run --no-project python scripts/release/verify_component_release.py --tag cli-vX.Y.Z`
4. Merge into `main`.
5. Create and push tag:

```bash
git tag cli-vX.Y.Z
git push origin cli-vX.Y.Z
```

6. Approve `pypi` environment when prompted.
7. Post-publish smoke:
   - `uvx --from psa-strategy-cli==X.Y.Z psa --version`

## Post-release verification (CLI)

Run on a machine with `uv`:

```bash
uvx --from psa-strategy-cli==X.Y.Z psa --version
uvx --from psa-strategy-cli==X.Y.Z psa strategy upsert \
  --strategy-id smoke \
  --input examples/strategy_bear.json \
  --json
uvx --from psa-strategy-cli==X.Y.Z psa evaluate-point \
  --strategy-id smoke \
  --input examples/evaluate_point_input.json \
  --output - \
  --json
uv tool install psa-strategy-cli==X.Y.Z
psa --version
```

## Failure scenarios

1. Validator fails before publish:
   - fix version/dependency mismatch;
   - push corrected commit and use a new tag.
2. CLI dependency policy fails:
   - replace exact pin with compatibility range;
   - rerun validator and retag.
3. Post-publish smoke cannot find package immediately:
   - wait for index propagation;
   - rerun smoke after a short delay.
4. Critical bug after publish:
   - create patch release;
   - do not overwrite existing files in PyPI.
