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

LABEL org.opencontainers.image.title="ra-hcp-frontend" \
      org.opencontainers.image.description="HCP admin UI (SvelteKit SSR on Bun, distroless)" \
      org.opencontainers.image.source="https://github.com/AI-Riksarkivet/ra-hcp" \
      org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# build/ is fully bundled by svelte-adapter-bun — no node_modules needed at runtime
COPY --from=builder /app/build /app/build

# svelte-adapter-bun listens on PORT (default 3000)
ENV PORT=3000

# svelte-adapter-bun defaults the request body limit to 512K, which would reject
# the simple (non-multipart) upload proxy path for any file >512K. Uploads >=100MB
# already go browser->S3 via presigned multipart (bypassing this proxy), so 256M
# comfortably covers the simple path.
ENV BODY_SIZE_LIMIT=256M

# Bun writes its runtime cache to $HOME. Under a non-root UID with no /etc/passwd
# entry (e.g. k8s podSecurityContext.runAsUser), $HOME falls back to "/" which
# isn't writable → "bun is unable to write files: AccessDenied". Point HOME at
# the world-writable /tmp so it works regardless of the runtime UID.
ENV HOME=/tmp

EXPOSE 3000

# Run as a non-root UID (distroless has no shell to create a named user; the
# build/ files are world-readable and 3000 is unprivileged, so a numeric UID
# works). Container-security best practice + satisfies non-root scan policies.
USER 65532:65532

CMD ["./build/index.js"]
