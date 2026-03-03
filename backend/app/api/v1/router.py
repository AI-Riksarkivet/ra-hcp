"""Aggregated API v1 router — S3 + MAPI endpoints."""

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.api.v1.endpoints import auth
from app.api.v1.endpoints.s3 import buckets, objects
from app.api.v1.endpoints.mapi import (
    tenants,
    namespaces,
    user_accounts,
    group_accounts,
    content_classes,
    retention_classes,
    replication,
    erasure_coding,
    statistics,
    logs,
    health_check,
    licenses,
    network,
    support,
)

api_router = APIRouter()

# ── Auth (public — no token required) ────────────────────────────────
api_router.include_router(auth.router)

# ── All routes below require authentication ──────────────────────────
_auth = [Depends(get_current_user)]

# ── S3 data-plane ────────────────────────────────────────────────────
api_router.include_router(buckets.router, dependencies=_auth)
api_router.include_router(objects.router, dependencies=_auth)

# ── Tenant-level MAPI (usable with a tenant admin account) ──────────
api_router.include_router(tenants.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(namespaces.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(user_accounts.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(group_accounts.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(content_classes.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(retention_classes.router, prefix="/mapi", dependencies=_auth)

# ── System-level MAPI (requires HCP system admin) ───────────────────
api_router.include_router(
    user_accounts.system_router, prefix="/mapi", dependencies=_auth
)
api_router.include_router(
    group_accounts.system_router, prefix="/mapi", dependencies=_auth
)
api_router.include_router(replication.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(erasure_coding.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(statistics.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(logs.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(health_check.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(licenses.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(network.router, prefix="/mapi", dependencies=_auth)
api_router.include_router(support.router, prefix="/mapi", dependencies=_auth)
