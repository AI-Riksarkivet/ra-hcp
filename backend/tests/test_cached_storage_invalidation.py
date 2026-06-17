"""Cross-instance cache invalidation for CachedStorage.

Regression test for the multi-worker/replica staleness bug: invalidation must
work when the reader and the writer are *different* CachedStorage instances
sharing one cache store (as happens across gunicorn workers / pod replicas).
Previously invalidation used an in-process dict, so a mutation on one instance
could not invalidate another instance's cached listing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

from key_value.aio.stores.memory import MemoryStore

from app.core.config import CacheSettings
from app.services.cached_storage import CachedStorage
from app.services.kv import KVCache


def _make_inner() -> AsyncMock:
    inner = AsyncMock()
    inner.list_objects.return_value = {
        "Contents": [{"Key": "k.jpg"}],
        "KeyCount": 1,
        "IsTruncated": False,
    }
    inner.delete_object.return_value = {}
    inner.delete_bucket.return_value = {}
    inner.put_object.return_value = None
    return inner


def _shared_cache() -> KVCache:
    return KVCache(MemoryStore(), enabled=True, has_url=True)


async def test_list_objects_served_from_cache_within_instance():
    inner = _make_inner()
    cs = CachedStorage(inner, _shared_cache(), CacheSettings())

    await cs.list_objects("b")
    await cs.list_objects("b")

    assert inner.list_objects.call_count == 1  # second call served from cache


async def test_delete_object_invalidates_list_across_instances():
    cache = _shared_cache()
    reader_inner = _make_inner()
    reader = CachedStorage(reader_inner, cache, CacheSettings())
    writer = CachedStorage(_make_inner(), cache, CacheSettings())

    await reader.list_objects("b")
    await reader.list_objects("b")
    assert reader_inner.list_objects.call_count == 1  # cached

    # A mutation on a *different* instance must invalidate the reader's cache.
    await writer.delete_object("b", "k.jpg")

    await reader.list_objects("b")
    assert reader_inner.list_objects.call_count == 2  # cross-instance miss → fresh


async def test_put_object_invalidates_list_across_instances():
    cache = _shared_cache()
    reader_inner = _make_inner()
    reader = CachedStorage(reader_inner, cache, CacheSettings())
    writer = CachedStorage(_make_inner(), cache, CacheSettings())

    await reader.list_objects("b")
    assert reader_inner.list_objects.call_count == 1

    await writer.put_object("b", "new.jpg", AsyncMock())

    await reader.list_objects("b")
    assert reader_inner.list_objects.call_count == 2


async def test_delete_bucket_invalidates_bucket_listing_across_instances():
    cache = _shared_cache()
    reader_inner = _make_inner()
    reader = CachedStorage(reader_inner, cache, CacheSettings())
    writer = CachedStorage(_make_inner(), cache, CacheSettings())

    await reader.list_objects("b")
    assert reader_inner.list_objects.call_count == 1

    await writer.delete_bucket("b")

    await reader.list_objects("b")
    assert reader_inner.list_objects.call_count == 2


async def test_empty_listing_is_not_cached():
    """A transient empty read must not poison the folder view for the TTL."""
    inner = _make_inner()
    inner.list_objects.return_value = {
        "Contents": [],
        "KeyCount": 0,
        "IsTruncated": False,
    }
    cs = CachedStorage(inner, _shared_cache(), CacheSettings())

    await cs.list_objects("b")
    await cs.list_objects("b")

    # Empty listings are never cached → the second call re-fetches (self-heals).
    assert inner.list_objects.call_count == 2
