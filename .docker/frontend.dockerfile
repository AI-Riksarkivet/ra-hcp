# syntax=docker/dockerfile:1
FROM denoland/deno:latest AS builder

WORKDIR /app

# Install dependencies first (cache-friendly)
COPY frontend/deno.json frontend/deno.lock frontend/package.json ./
RUN deno install

# Copy source and build
COPY frontend/ .
RUN deno task build

# ── Production stage ─────────────────────────────────────────────────
FROM denoland/deno:latest

RUN groupadd --system app 2>/dev/null; useradd --system --gid app app 2>/dev/null || true

WORKDIR /app
COPY --from=builder /app/build /app/build
COPY --from=builder /app/deno.json /app/deno.lock /app/package.json /app/

USER app

EXPOSE 3000

CMD ["deno", "task", "preview", "--host", "0.0.0.0", "--port", "3000"]
