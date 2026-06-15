"""Tests for the optional-MAPI deployment flag (MAPI_ENABLED).

The flag defaults to True so existing HCP deployments are unchanged. Setting
MAPI_ENABLED=false yields an S3-only deployment (e.g. against MinIO): the MAPI/
tenant/namespace/query routers are not mounted and /capabilities reports it.
"""

from __future__ import annotations

import importlib

import pytest
from httpx import AsyncClient


async def test_capabilities_reports_mapi_enabled_by_default(client: AsyncClient):
    resp = await client.get("/api/v1/capabilities")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mapi_enabled"] is True
    assert "storage_backend" in body


async def test_capabilities_reflects_mapi_disabled(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("MAPI_ENABLED", "false")
    resp = await client.get("/api/v1/capabilities")
    assert resp.status_code == 200
    assert resp.json()["mapi_enabled"] is False


async def test_mapi_routers_mounted_by_default(client: AsyncClient):
    # A MAPI route exists when enabled — unauthenticated requests get 401/403,
    # never 404. We assert behaviour (route is reachable) rather than poking
    # FastAPI's internal route objects, which changed shape in 0.137.
    assert (await client.get("/api/v1/mapi/tenants")).status_code != 404
    # S3 data-plane is always mounted.
    assert (await client.get("/api/v1/buckets")).status_code != 404


async def test_mapi_routers_absent_when_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MAPI_ENABLED", "false")
    import app.api.v1.router as router_mod

    importlib.reload(router_mod)
    try:
        # Build a fresh app from the reloaded (MAPI-disabled) router and assert
        # MAPI/query routes 404 while the S3 data-plane stays mounted.
        from fastapi import FastAPI
        from httpx import ASGITransport

        test_app = FastAPI()
        test_app.include_router(router_mod.api_router, prefix="/api/v1")
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            assert (await ac.get("/api/v1/mapi/tenants")).status_code == 404
            assert (await ac.get("/api/v1/query/search")).status_code == 404
            assert (await ac.get("/api/v1/buckets")).status_code != 404
    finally:
        # Restore the default-enabled router so other tests are unaffected.
        monkeypatch.delenv("MAPI_ENABLED", raising=False)
        importlib.reload(router_mod)
