# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.10.9-python3.13-trixie-slim AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --extra serve --extra lance

# Copy application code
COPY backend/ .
RUN uv sync --frozen --extra serve --extra lance

# ── Production stage ─────────────────────────────────────────────────
FROM python:3.13-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH"
ENV REDIS_URL=""

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/liveness')"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
