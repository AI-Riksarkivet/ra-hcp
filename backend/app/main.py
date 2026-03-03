"""HCP Unified API — S3 data-plane + MAPI admin."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.dependencies import get_cache_service
from app.api.v1.router import api_router
from app.core.config import AuthSettings
from app.core.telemetry import setup_telemetry
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.config import CacheSettings, MapiSettings
    from app.services.cache_service import CacheService
    from app.services.mapi_service import MapiService

    # ── Startup ──────────────────────────────────────────────────────
    cache_settings = CacheSettings()
    cache = CacheService(cache_settings)
    await cache.connect()
    app.state.cache = cache

    mapi_settings = MapiSettings()
    if cache.enabled:
        from app.services.cached_mapi import CachedMapiService

        logger.info("Creating CachedMapiService singleton")
        app.state.mapi = CachedMapiService(mapi_settings, cache, cache_settings)
    else:
        logger.info("Creating MapiService singleton")
        app.state.mapi = MapiService(mapi_settings)

    app.state.s3_cache = {}

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    await app.state.mapi.close()
    await cache.close()


ROOT_PATH = os.getenv("ROOT_PATH", "")

OPENAPI_TAGS = [
    # ── Public ──
    {
        "name": "Authentication",
        "description": "Login to obtain a JWT token.",
    },
    {
        "name": "Health",
        "description": "Application health check.",
    },
    # ── S3 data-plane ──
    {
        "name": "S3 Buckets",
        "description": "Create, list, and manage S3 buckets (versioning, ACLs).",
    },
    {
        "name": "S3 Objects",
        "description": "Upload, download, copy, and delete objects within buckets.",
    },
    # ── System Admin (requires HCP system admin) ──
    {
        "name": "System Admin: Tenants",
        "description": "List and create tenants. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Admin: Identity",
        "description": "Manage system-level user and group accounts. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Admin: Infrastructure",
        "description": "View and manage network settings, licenses, and system statistics. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Admin: Operations",
        "description": "Run health checks, prepare and download logs, and manage support access. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Admin: Replication",
        "description": "Manage replication links, certificates, and schedules. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Admin: Erasure Coding",
        "description": "Manage erasure-coding topologies. "
        "**Requires: system-level user account.**",
    },
    # ── Tenant Admin (requires tenant admin role) ──
    {
        "name": "Tenant Admin: Settings",
        "description": "View and modify tenant configuration: console security, contact info, "
        "email notifications, namespace defaults, search security, permissions, "
        "service plans, CORS. **Requires: tenant-level admin role.**",
    },
    {
        "name": "Tenant Admin: Statistics",
        "description": "View tenant statistics and chargeback reports. "
        "**Requires: tenant-level monitor role.**",
    },
    {
        "name": "Tenant Admin: Identity",
        "description": "Manage tenant-level user and group accounts: create, modify, delete, "
        "reset passwords, and assign per-bucket data access permissions. "
        "**Requires: tenant-level security role.**",
    },
    {
        "name": "Tenant Admin: Content Classes",
        "description": "Manage content classes for your tenant. "
        "**Requires: tenant-level admin role.**",
    },
    # ── Namespace (requires admin/compliance role within tenant) ──
    {
        "name": "Namespace: Management",
        "description": "Create, list, and manage namespaces and versioning settings. "
        "**Requires: tenant-level admin role.**",
    },
    {
        "name": "Namespace: Compliance",
        "description": "Manage compliance settings and retention classes per namespace. "
        "**Requires: tenant-level compliance role.**",
    },
    {
        "name": "Namespace: Access",
        "description": "Manage namespace permissions, protocol configuration (HTTP/REST, NFS, "
        "CIFS, SMTP), CORS, and replication collision settings. "
        "**Requires: tenant-level admin role.**",
    },
    {
        "name": "Namespace: Indexing",
        "description": "Manage custom metadata indexing settings. "
        "**Requires: tenant-level admin role.**",
    },
    {
        "name": "Namespace: Statistics",
        "description": "View namespace statistics and chargeback reports. "
        "**Requires: tenant-level monitor role.**",
    },
]

app = FastAPI(
    title="HCP Unified API",
    description=(
        "S3 data-plane + MAPI admin for Hitachi Content Platform.\n\n"
        "## Access levels\n\n"
        "- **S3 Buckets / S3 Objects** — S3 data operations\n"
        "- **System Admin: \u2026** — system-level MAPI (requires HCP system admin)\n"
        "- **Tenant Admin: \u2026** — tenant-level MAPI (requires tenant admin role)\n"
        "- **Namespace: \u2026** — namespace-level MAPI "
        "(requires admin/compliance role within tenant)\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    root_path=ROOT_PATH,
    openapi_tags=OPENAPI_TAGS,
)

# ── Telemetry ─────────────────────────────────────────────────────────
setup_telemetry(app)

# ── Middleware (outermost first) ──────────────────────────────────────

# Request ID — outermost so every response gets an ID
app.add_middleware(RequestIDMiddleware)  # type: ignore[arg-type]

# GZip — compress responses > 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)  # type: ignore[arg-type]

# CORS — use CORS_ORIGINS env var; empty = allow all (dev mode)
_auth_settings = AuthSettings()
_cors_origins = [o.strip() for o in _auth_settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=_cors_origins or ["*"],
    allow_credentials=bool(_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception(
        "Unhandled exception on %s %s [request_id=%s]",
        request.method,
        request.url.path,
        request_id,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


# ── Mount API routes ──────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Health endpoint ───────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health(cache: CacheService | None = Depends(get_cache_service)):
    return {
        "status": "ok",
        "cache": "connected" if cache and cache.enabled else "disabled",
    }
