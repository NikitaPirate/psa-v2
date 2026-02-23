# Contracts

Machine-facing payload contracts are versioned JSON Schema files under `schemas/`.

## Request schemas

Evaluate payloads (strategy supplied by CLI `--strategy-id`):
- `schemas/evaluate_point.request.v1.json`
- `schemas/evaluate_rows.request.v1.json`
- `schemas/evaluate_rows_from_ranges.request.v1.json`

Storage mutations:
- `schemas/strategy_upsert.request.v1.json`
- `schemas/log_append.request.v1.json`

## Response schemas

Evaluation responses:
- `schemas/evaluate_point.response.v1.json`
- `schemas/evaluate_rows.response.v1.json`

Strategy/log responses are CLI-defined JSON payloads validated by integration tests.

## CLI contract notes

- All operational commands require `--json`.
- Success payload is JSON.
- Error payload format is:
  - `error.code`
  - `error.message`
  - `error.details`
- Exit code `0` means success; any non-zero code means failure.

### `install-skill` command

- Command form: `psa install-skill <runtime> --json`.
- Runtime id is validated by parser choices (see `psa install-skill --help`).
- Success payload includes:
  - `runtime`, `runtime_name`, `skill`, `dest`,
  - `files_installed`, `files_skipped`,
  - optional `agents_config` when runtime has extra agent config target.

## Data contract notes

- Time fields use ISO-8601 date-time strings with timezone.
- `market_mode` enum is fixed to `bear | bull`.
- Output shares are normalized to `[0, 1]`.
- `price_segments` must include at least one row with `weight > 0`.
- Schema checks structure and primitive constraints.
- Cross-field and semantic constraints are enforced in `core/src/psa_core/validation.py`.

## Runtime adapters

`core/src/psa_core/contracts.py` exposes evaluation payload adapters:
- request parsing,
- runtime validation delegation,
- JSON-ready response building.
