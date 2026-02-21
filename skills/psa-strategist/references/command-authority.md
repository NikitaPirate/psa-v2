# Command Authority

This file is the single source of truth for operational command permissions in `psa-strategist`.

## Core Rule
Use only the approved command surface below.
When environment/tooling limitations prevent direct execution, auxiliary commands are allowed only if they are minimally necessary to run `psa` commands.

## Approved Command Surface

### Domain operations (primary path)
- `psa ...`

This includes all strategy, log, and evaluation operations.

### Runtime bootstrap exceptions (only when `psa` is unavailable)
- `psa --version`
- `uv tool install psa-strategy-cli`
- `uv tool update-shell`

## User Input Rule
Do not require the user to create service/intermediate files for normal flow.
When payload input is needed, prefer `psa ... --input - ...` with command stdin.
If direct stdin transport is unavailable in the current execution environment, use the minimal auxiliary mechanism required to pass payload into the same `psa` command.

## Blocker Rule
If `psa` cannot run and bootstrap exceptions cannot resolve runtime, stop and report:
- "PSA CLI cannot run in this environment because `uv` or PATH configuration is missing. Install/configure `uv`, then I can continue."
