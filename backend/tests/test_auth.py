"""Tests for the authentication endpoint."""

from __future__ import annotations

from httpx import AsyncClient


async def test_login_with_valid_credentials(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "testpass"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_with_wrong_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "wrongpass"},
    )
    assert resp.status_code == 401
    assert "Invalid username or password" in resp.json()["detail"]


async def test_login_with_wrong_username(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "wronguser", "password": "testpass"},
    )
    assert resp.status_code == 401


async def test_login_token_can_access_protected_route(client: AsyncClient):
    # Get a token
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "testuser", "password": "testpass"},
    )
    token = login_resp.json()["access_token"]

    # Use token to access a protected route
    resp = await client.get(
        "/api/v1/buckets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


async def test_protected_route_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/buckets")
    assert resp.status_code == 401


async def test_protected_route_with_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/buckets",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
