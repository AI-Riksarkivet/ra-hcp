"""Tests for app.core.security JWT functions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.core.config import AuthSettings
from app.core.security import create_access_token, verify_token


_TEST_KEY = "test-secret-key-for-unit-tests-min32b"


@pytest.fixture
def settings() -> AuthSettings:
    return AuthSettings(api_secret_key=_TEST_KEY, api_token_expire_minutes=60)


def test_create_access_token_returns_valid_jwt(settings: AuthSettings):
    token = create_access_token("alice", settings=settings)
    payload = pyjwt.decode(token, _TEST_KEY, algorithms=["HS256"])
    assert payload["sub"] == "alice"
    assert "exp" in payload


def test_create_access_token_expiry_matches_settings(settings: AuthSettings):
    before = datetime.now(timezone.utc)
    token = create_access_token("alice", settings=settings)
    after = datetime.now(timezone.utc)

    payload = pyjwt.decode(token, _TEST_KEY, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    assert exp >= before + timedelta(minutes=59)
    assert exp <= after + timedelta(minutes=61)


def test_verify_token_returns_username(settings: AuthSettings):
    token = create_access_token("alice", settings=settings)
    username = verify_token(token, settings=settings)
    assert username == "alice"


def test_verify_token_rejects_expired_token(settings: AuthSettings):
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    payload = {"sub": "alice", "exp": expire}
    token = pyjwt.encode(payload, _TEST_KEY, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, settings=settings)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_verify_token_rejects_invalid_signature(settings: AuthSettings):
    token = pyjwt.encode(
        {"sub": "alice", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong-key-that-is-at-least-32-bytes!",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, settings=settings)
    assert exc_info.value.status_code == 401


def test_verify_token_rejects_missing_subject(settings: AuthSettings):
    payload = {"exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    token = pyjwt.encode(payload, _TEST_KEY, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, settings=settings)
    assert exc_info.value.status_code == 401
    assert "no subject" in exc_info.value.detail.lower()


def test_verify_token_rejects_garbage():
    with pytest.raises(HTTPException) as exc_info:
        verify_token("not.a.jwt")
    assert exc_info.value.status_code == 401
