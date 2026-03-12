# syntax=docker/dockerfile:1
FROM denoland/deno:2.7.1 AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY frontend/deno.json frontend/deno.lock frontend/package.json ./
RUN deno install

# Copy source and build
COPY frontend/ .
RUN deno task build

# ── Production stage ─────────────────────────────────────────────────
FROM denoland/deno:2.7.1

RUN groupadd -g 1000 app 2>/dev/null || true && \
    useradd -u 1000 -g 1000 -s /bin/sh app 2>/dev/null || true

WORKDIR /app
COPY --from=builder --chown=1000:1000 /app/.deno-deploy /app/.deno-deploy
COPY --from=builder --chown=1000:1000 /app/node_modules /app/node_modules
COPY --from=builder --chown=1000:1000 /app/deno.json /app/deno.lock /app/package.json /app/

USER 1000

EXPOSE 8000

CMD ["deno", "run", "-A", ".deno-deploy/server.ts"]
