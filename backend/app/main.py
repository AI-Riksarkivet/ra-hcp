"""HCP Unified API — S3 data-plane + MAPI admin."""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import metrics, trace
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.dependencies import get_cache_service
from app.api.v1.router import api_router
from app.core.config import AuthSettings
from app.core.telemetry import setup_telemetry
from app.services.kv import KVCache, create_kv_cache
from app.services.mapi_errors import MapiError

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

# Paths that are called constantly by probes — skip access logging
_HEALTH_PATHS = frozenset({"/healthz", "/readyz", "/health"})

_meter = metrics.get_meter(__name__)
_http_request_duration = _meter.create_histogram(
    "http.server.request.duration",
    description="HTTP request duration in milliseconds",
    unit="ms",
)
_http_request_count = _meter.create_counter(
    "http.server.request.count",
    description="Total HTTP requests",
    unit="1",
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Request ID, OTel trace correlation, and per-request access logging."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        # Correlate request_id with OTel trace
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("request.id", request_id)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Request-ID"] = request_id

        # Record HTTP metrics
        metric_attrs = {
            "http.method": request.method,
            "http.status_code": response.status_code,
            "http.route": request.url.path,
        }
        _http_request_duration.record(duration_ms, metric_attrs)
        _http_request_count.add(1, metric_attrs)

        # Log all non-health requests
        if request.url.path not in _HEALTH_PATHS:
            # Extract trace/span IDs for log correlation
            ctx = span.get_span_context()
            trace_id = format(ctx.trace_id, "032x") if ctx.trace_id else None
            span_id = format(ctx.span_id, "016x") if ctx.span_id else None

            # Best-effort user/tenant extraction from JWT (no validation)
            user = None
            tenant = None
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                try:
                    import jwt

                    payload = jwt.decode(auth[7:], options={"verify_signature": False})
                    user = payload.get("sub")
                    tenant = payload.get("tenant")
                except Exception:
                    pass

            access_logger.info(
                "%s %s %s %sms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params) or None,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "user": user,
                    "tenant": tenant,
                    "client_ip": request.client.host if request.client else None,
                    "trace_id": trace_id,
                    "span_id": span_id,
                },
            )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.config import CacheSettings, MapiSettings
    from app.services.mapi_service import MapiService
    from app.services.query_service import QueryService

    # ── Startup ──────────────────────────────────────────────────────
    cache_settings = CacheSettings()
    cache = create_kv_cache(cache_settings)
    await cache.connect()
    app.state.cache = cache

    mapi_settings = MapiSettings()
    mapi = MapiService(mapi_settings)
    if cache.enabled:
        from app.services.cached_mapi import CachedMapiService

        logger.info("Creating CachedMapiService singleton")
        app.state.mapi = CachedMapiService(mapi, cache, cache_settings)
    else:
        logger.info("Creating MapiService singleton")
        app.state.mapi = mapi

    app.state.s3_cache = {}
    app.state.lance_cache = {}

    query = QueryService(mapi_settings)
    if cache.enabled:
        from app.services.cached_query import CachedQueryService

        logger.info("Creating CachedQueryService singleton")
        app.state.query = CachedQueryService(query, cache, cache_settings)
    else:
        logger.info("Creating QueryService singleton")
        app.state.query = query

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    # Close all cached S3 storage adapters
    for storage in app.state.s3_cache.values():
        try:
            await storage.close()
        except Exception:
            logger.warning("Failed to close S3 storage adapter", exc_info=True)

    await app.state.query.close()
    await app.state.mapi.close()
    await cache.close()


ROOT_PATH = os.getenv("ROOT_PATH", "")

OPENAPI_TAGS = [
    # ── Public ──
    {
        "name": "Authentication",
        "description": (
            "Login to obtain a JWT token.\n\n"
            "Use the **Authorize** lock icon (top-right) to log in. "
            "For tenant-scoped access, enter `tenant/username` in the username field "
            "(e.g. `dev-ai/admin`)."
        ),
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
    {
        "name": "S3 Credentials",
        "description": "Generate presigned URLs and retrieve S3 access credentials.",
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
    # ── Metadata Query API ──
    {
        "name": "Metadata Query",
        "description": "Search objects by metadata and audit create/delete/purge events "
        "via the HCP Metadata Query API.",
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


# ── Domain exception handlers ─────────────────────────────────────────
#
# Translate service-layer domain exceptions into HTTP responses so that
# endpoints don't need explicit try/except for every call.


@app.exception_handler(MapiError)
async def mapi_error_handler(request: Request, exc: MapiError):
    return JSONResponse(
        status_code=exc.http_status,
        content={"detail": exc.message},
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


# ── Health & readiness probes ─────────────────────────────────────────


@app.get("/healthz", tags=["Health"])
async def healthz():
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "ok"}


@app.get("/readyz", tags=["Health"])
async def readyz(request: Request):
    """Readiness probe — checks backend services are reachable."""
    from app.core.config import StorageSettings

    checks: dict[str, str] = {}
    ready = True

    storage_settings = StorageSettings()

    # HCP MAPI check (only when backend is HCP)
    if storage_settings.storage_backend == "hcp":
        mapi = getattr(request.app.state, "mapi", None)
        if mapi is not None and await mapi.ping():
            checks["hcp"] = "reachable"
        else:
            checks["hcp"] = "unreachable"
            ready = False
    else:
        checks["storage"] = storage_settings.storage_backend

    # Cache (required only when configured)
    cache: KVCache | None = getattr(request.app.state, "cache", None)
    if cache is not None and cache.has_url:
        if await cache.ping():
            checks["cache"] = "connected"
        else:
            checks["cache"] = "disconnected"
            ready = False
    else:
        checks["cache"] = "disabled"

    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not ready", "checks": checks},
    )


@app.get("/health", tags=["Health"])
async def health(cache: KVCache | None = Depends(get_cache_service)):
    """Legacy health endpoint (backwards compatible)."""
    return {
        "status": "ok",
        "cache": "connected" if cache and cache.enabled else "disabled",
    }
