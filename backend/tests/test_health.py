"""Tests for health and readiness probe endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
from httpx import ASGITransport, AsyncClient

from tests.conftest import HCP_BASE


# ── /healthz (liveness) ──────────────────────────────────────────────


async def test_healthz_returns_ok(client: AsyncClient):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_healthz_does_not_require_auth(client: AsyncClient):
    resp = await client.get("/healthz")
    assert resp.status_code == 200


# ── /readyz (readiness) ──────────────────────────────────────────────


async def test_readyz_ready_when_hcp_reachable(client: AsyncClient, hcp_mock):
    hcp_mock.head(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200),
    )
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["checks"]["hcp"] == "reachable"


async def test_readyz_not_ready_when_hcp_unreachable(client: AsyncClient):
    # Mock ping to return False (HCP unreachable)
    transport = client._transport
    assert isinstance(transport, ASGITransport)
    app = transport.app
    with patch.object(
        app.state.mapi,  # type: ignore[union-attr]
        "ping",
        new_callable=AsyncMock,
        return_value=False,
    ):
        resp = await client.get("/readyz")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "not ready"
    assert data["checks"]["hcp"] == "unreachable"


async def test_readyz_does_not_require_auth(client: AsyncClient, hcp_mock):
    hcp_mock.head(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200),
    )
    resp = await client.get("/readyz")
    assert resp.status_code == 200


async def test_readyz_cache_disabled_is_ok(client: AsyncClient, hcp_mock):
    """When no Redis is configured, cache shows disabled and readiness passes."""
    hcp_mock.head(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200),
    )
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["checks"]["cache"] == "disabled"


# ── /health (legacy) ─────────────────────────────────────────────────


async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "cache" in data


async def test_health_does_not_require_auth(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
