# syntax=docker/dockerfile:1
FROM oven/bun:1.2-slim AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile

# Copy source and build (svelte-adapter-bun emits a self-contained build/index.js)
COPY frontend/ .
RUN bun run build

# ── Production stage ─────────────────────────────────────────────────
FROM oven/bun:1.2-slim

# Apply available OS security patches (openssl, glibc/libc6, zlib, etc.) so the
# image ships with the latest fixed Debian packages. Trivy gates these CVEs in
# CI (`make scan`).
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# build/ is fully bundled by svelte-adapter-bun — no node_modules needed at runtime
COPY --from=builder --chown=bun:bun /app/build /app/build

# svelte-adapter-bun listens on PORT (default 3000)
ENV PORT=3000

USER bun

EXPOSE 3000

CMD ["bun", "./build/index.js"]
