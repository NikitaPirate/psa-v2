from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from psa_api.errors import register_exception_handlers
from psa_api.routes import router as v1_router
from psa_api.schema_validation import initialize_request_schema_validator


@asynccontextmanager
async def _lifespan(app: FastAPI):
    del app
    initialize_request_schema_validator()
    yield


app = FastAPI(title="psa-api", version="0.1.0", lifespan=_lifespan)
register_exception_handlers(app)
app.include_router(v1_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
