# syntax=docker/dockerfile:1
FROM oven/bun:1.2-slim AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY frontend/package.json frontend/bun.lock* ./
RUN bun install --frozen-lockfile

# Copy source and build (svelte-adapter-bun emits a self-contained build/index.js)
COPY frontend/ .
RUN bun run build

# ── Production stage (distroless) ────────────────────────────────────
# Distroless has no shell/apt/perl/zlib-dev, so it ships with zero HIGH/CRITICAL
# OS CVEs (vs ~21 on the Debian -slim base). The svelte-adapter-bun build is
# fully self-contained (no node_modules at runtime), so nothing here needs a
# package manager. The image entrypoint is already /usr/local/bin/bun, so CMD
# just passes the server entry as its argument.
FROM oven/bun:1.2-distroless@sha256:e2c3f36733fa2c2c9c80d89b481d9fc7629558cac2533c776f6285ae1ba6b8fa

WORKDIR /app

# build/ is fully bundled by svelte-adapter-bun — no node_modules needed at runtime
COPY --from=builder /app/build /app/build

# svelte-adapter-bun listens on PORT (default 3000)
ENV PORT=3000

EXPOSE 3000

CMD ["./build/index.js"]
