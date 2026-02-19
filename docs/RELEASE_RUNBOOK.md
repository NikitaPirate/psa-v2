# Release Runbook (`psa-strategy-core` + `psa-strategy-cli`)

This runbook documents the tag-driven release process for `psa-v2`.

## Scope

- `psa-strategy-core` and `psa-strategy-cli` are released from the same repository.
- Versioning is lockstep: both packages share the same `X.Y.Z`.
- Releases are triggered by pushing a git tag `vX.Y.Z`.
- GitHub Releases are optional and not required by this workflow.

## One-time setup

1. Configure PyPI projects:
   - `psa-strategy-core`
   - `psa-strategy-cli`
2. Configure trusted publishing for both projects from this GitHub repository/workflow.
3. Create GitHub Environment `pypi` with required reviewers.
4. Enable branch protection so CI must pass before merge.

## Version bump checklist

For a new release `X.Y.Z`:

1. Update `/core/pyproject.toml`:
   - `[project].version = "X.Y.Z"`
2. Update `/cli/pyproject.toml`:
   - `[project].version = "X.Y.Z"`
   - dependency `psa-strategy-core==X.Y.Z`
3. Validate lockstep locally:
   - `uv run python scripts/release/verify_release_state.py --tag vX.Y.Z`

## Pre-tag validation

Run from repository root:

```bash
uv sync
uv run ruff check .
uv run pytest
uv build --package psa-strategy-core --out-dir dist/core
uv build --package psa-strategy-cli --out-dir dist/cli
uvx --from dist/cli/*.whl --with dist/core/*.whl psa --version
uvx --from dist/cli/*.whl --with dist/core/*.whl psa evaluate-point \
  --input examples/bear_accumulate_point.json \
  --output -
```

## Release flow (tags)

1. Merge release changes into `main`.
2. Create and push tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

3. GitHub Actions workflow `Publish` starts automatically.
4. Approve `pypi` environment when prompted.
5. Workflow publishes in strict order:
   - `psa-strategy-core`
   - `psa-strategy-cli`
6. Workflow runs post-publish smoke:
   - `uvx --from psa-strategy-cli==X.Y.Z psa --version`

## Post-release verification

Run on a machine with `uv`:

```bash
uvx --from psa-strategy-cli==X.Y.Z psa --version
uvx --from psa-strategy-cli==X.Y.Z psa evaluate-point --input examples/bear_accumulate_point.json --output -
uv tool install psa-strategy-cli==X.Y.Z
psa --version
```

## Failure scenarios

1. Lockstep validation fails before publish:
   - fix versions/dependency mismatch;
   - push corrected commit and a new tag.
2. `psa-strategy-core` published, `psa-strategy-cli` failed:
   - fix issue and rerun workflow if possible;
   - if rerun cannot complete reliably, bump to next patch version and retag.
3. Post-publish smoke cannot find package immediately:
   - wait for index propagation;
   - rerun smoke after a short delay.
4. Critical bug after publish:
   - create patch release `X.Y.(Z+1)`;
   - do not overwrite existing files in PyPI.
