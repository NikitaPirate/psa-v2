# PSA Web POC

Local `Transfer & Evaluate` screen for M1 POC.

## Commands

```bash
npm install
npm run dev
npm run test -- --run
npm run build
```

## Scope

- canonical strategy JSON payload (`strategy_upsert.request.v1.json` shape);
- bidirectional JSON text area (paste/copy) + upload/download `.json`;
- price slider -> `POST /v1/evaluate/point`;
- show `target_share` and `base_share`.

Timestamp is fixed in code on purpose for POC.
