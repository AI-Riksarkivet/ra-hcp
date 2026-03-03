"""Tests for the health endpoint."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "cache" in data


async def test_health_does_not_require_auth(client: AsyncClient):
    # No auth headers — should still succeed
    resp = await client.get("/health")
    assert resp.status_code == 200
