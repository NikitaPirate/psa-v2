FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/core/src:/app/api/src

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install "fastapi>=0.115.0" "jsonschema>=4.25.0" "uvicorn>=0.30.0"

COPY core/src /app/core/src
COPY api/src /app/api/src
COPY schemas /app/schemas

EXPOSE 8000

CMD ["uvicorn", "psa_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
