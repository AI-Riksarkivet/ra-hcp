"""HCP Unified API — S3 data-plane + MAPI admin."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.telemetry import setup_telemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Close the MAPI httpx client on shutdown
    from app.api import dependencies

    if dependencies._mapi_instance is not None:
        await dependencies._mapi_instance.close()
        dependencies._mapi_instance = None


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
    # ── Tenant-level MAPI (your access) ──
    {
        "name": "Tenant Settings",
        "description": "View and modify tenant configuration: console security, contact info, "
        "email notifications, namespace defaults, search security, permissions, "
        "service plans, CORS. **Requires: tenant-level admin role.**",
    },
    {
        "name": "Namespaces",
        "description": "Create, list, and manage namespaces within your tenant. "
        "Includes protocol configuration (HTTP/REST, NFS, CIFS, SMTP), "
        "versioning, compliance, custom metadata indexing, permissions, CORS. "
        "**Requires: tenant-level admin role.**",
    },
    {
        "name": "User Accounts",
        "description": "Manage tenant-level user accounts: create, modify, delete users, "
        "reset passwords, and assign per-bucket data access permissions. "
        "**Requires: tenant-level security role.**",
    },
    {
        "name": "Group Accounts",
        "description": "Manage tenant-level group accounts: create, modify, delete groups, "
        "and assign per-bucket data access permissions. "
        "**Requires: tenant-level security role.**",
    },
    {
        "name": "Content Classes",
        "description": "Manage content classes for your tenant. "
        "**Requires: tenant-level admin role.**",
    },
    {
        "name": "Retention Classes",
        "description": "Manage retention classes per namespace. "
        "**Requires: tenant-level compliance role.**",
    },
    {
        "name": "Tenant Statistics",
        "description": "View tenant and namespace statistics and chargeback reports. "
        "**Requires: tenant-level monitor role.**",
    },
    # ── System-level MAPI (requires system admin) ──
    {
        "name": "System Tenants",
        "description": "List and create tenants. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System User Accounts",
        "description": "Manage system-level user accounts. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Group Accounts",
        "description": "Manage system-level group accounts. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Replication",
        "description": "Manage replication links, certificates, and schedules. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Erasure Coding",
        "description": "Manage erasure-coding topologies. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "System Statistics",
        "description": "View node and service statistics. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Health Check",
        "description": "Run and download system health check reports. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Licenses",
        "description": "View and upload storage licenses. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Network",
        "description": "View and modify network settings. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Support",
        "description": "Manage support access credentials. "
        "**Requires: system-level user account.**",
    },
    {
        "name": "Logs",
        "description": "Prepare and download system logs. "
        "**Requires: system-level user account.**",
    },
]

app = FastAPI(
    title="HCP Unified API",
    description=(
        "S3 data-plane + MAPI admin for Hitachi Content Platform.\n\n"
        "## Access levels\n\n"
        "- **S3 Buckets / S3 Objects** — S3 data operations\n"
        "- **Tenant \u2026** / **Namespaces** / **User Accounts** / **Group Accounts** / "
        "**Content Classes** / **Retention Classes** — "
        "tenant-level MAPI (usable with a tenant admin account)\n"
        "- **System \u2026** / **Replication** / **Erasure Coding** / **Health Check** / "
        "**Licenses** / **Network** / **Support** / **Logs** — "
        "system-level MAPI only (requires HCP system admin)\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    root_path=ROOT_PATH,
    openapi_tags=OPENAPI_TAGS,
)

# ── Telemetry ─────────────────────────────────────────────────────────
setup_telemetry(app)

# ── CORS ───────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Mount API routes ──────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Health endpoint ───────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
