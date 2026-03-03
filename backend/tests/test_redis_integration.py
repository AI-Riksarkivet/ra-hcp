"""Integration tests requiring a real Redis connection.

These tests are marked with ``@pytest.mark.redis`` and skipped
unless the ``REDIS_URL`` environment variable is set.  In CI they run
via ``dagger call test-integration --source=.`` which spins up a real
Redis sidecar.
"""

from __future__ import annotations

import os

import pytest

from app.core.config import CacheSettings
from app.services.cache_service import CacheService

REDIS_URL = os.environ.get("REDIS_URL", "")

pytestmark = [
    pytest.mark.redis,
    pytest.mark.skipif(not REDIS_URL, reason="REDIS_URL not set"),
]


@pytest.fixture
async def cache():
    settings = CacheSettings(
        redis_url=REDIS_URL,
        cache_key_prefix="integration-test",
        cache_default_ttl=10,
    )
    svc = CacheService(settings)
    await svc.connect()
    yield svc
    await svc.close()


async def test_real_redis_connect(cache: CacheService):
    """CacheService connects and reports enabled with a real Redis."""
    assert cache.enabled is True


async def test_real_redis_set_get_delete(cache: CacheService):
    """Round-trip set/get/delete against real Redis."""
    await cache.set("hello", {"msg": "world"})
    result = await cache.get("hello")
    assert result == {"msg": "world"}

    await cache.delete("hello")
    assert await cache.get("hello") is None
