# PSA Web

Local `Create / Use` client for PSA strategy editing and evaluation.

## Commands

```bash
npm install
npm run dev
npm run test -- --run
npm run build
```

## Scope

- canonical strategy JSON payload (`strategy_upsert.request.v1.json` shape);
- `Create` mode: JSON + form controls with explicit `Apply JSON`;
- `Use` mode: evaluate `now` and custom point (`timestamp`, `price`);
- docs mode (separate route, localized only inside docs):
  - `/docs/en`
  - `/docs/ru`
- charts use API/core only:
  - line via `POST /v1/evaluate/rows`;
  - heatmap + 3D via `POST /v1/evaluate/rows-from-ranges` (only when `time_segments` exist).
