# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.10.9-python3.13-trixie-slim@sha256:095668e9a6d4544b53e746b4f107889b13ce5cc6d01d65df5c6ac702ef5f457a AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --extra serve

# Copy application code
COPY backend/ .
RUN uv sync --frozen --extra serve

# ── Production stage ─────────────────────────────────────────────────
FROM python:3.13-slim@sha256:7d8999b140f22939451e00b79c0fd86f13d0bc0577b369f8212fce063101fb2a

LABEL org.opencontainers.image.title="ra-hcp" \
      org.opencontainers.image.description="HCP S3 + Management API gateway (FastAPI)" \
      org.opencontainers.image.source="https://github.com/AI-Riksarkivet/ra-hcp" \
      org.opencontainers.image.licenses="Apache-2.0"

# Apply available OS security patches (openssl, glibc/libc6, zlib, etc.) so the
# image ships with the latest fixed Debian packages rather than whatever the
# pinned base layer froze. Trivy gates these CVEs in CI (`make scan`).
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--max-requests", "10000", \
     "--max-requests-jitter", "1000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-"]
