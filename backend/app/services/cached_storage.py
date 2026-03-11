"""Composition-based caching wrapper for any StorageProtocol implementation.

Wraps any StorageProtocol via the decorator pattern. One class works with
any backend — HCP, MinIO, Ceph, AWS, or future adapters.
"""

from __future__ import annotations

import logging
from typing import IO

from opentelemetry import trace

from app.core.config import CacheSettings
from app.services.cache_service import CacheService
from app.services.storage.protocol import StorageProtocol

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CachedStorage:
    """Transparent caching wrapper for any StorageProtocol implementation."""

    def __init__(
        self,
        inner: StorageProtocol,
        cache: CacheService,
        cache_settings: CacheSettings,
    ):
        self._inner = inner
        self._cache = cache
        self._cs = cache_settings

    def _key(self, *parts: str) -> str:
        return "s3:" + ":".join(parts)

    # ── Cached reads ───────────────────────────────────────────────────

    def list_buckets(self) -> dict:
        with tracer.start_as_current_span("cached_s3.list_buckets") as span:
            key = self._key("list_buckets")
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.list_buckets()
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_list_ttl)
            return result

    def head_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "cached_s3.head_bucket", attributes={"s3.bucket": name}
        ) as span:
            key = self._key("head_bucket", name)
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.head_bucket(name)
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
        continuation_token: str | None = None,
        delimiter: str | None = None,
        fetch_owner: bool = True,
    ) -> dict:
        if continuation_token is not None:
            return self._inner.list_objects(
                bucket, prefix, max_keys, continuation_token, delimiter, fetch_owner
            )
        with tracer.start_as_current_span(
            "cached_s3.list_objects",
            attributes={"s3.bucket": bucket, "s3.prefix": prefix or ""},
        ) as span:
            key = self._key(
                "list_objects", bucket, prefix or "", delimiter or "", str(max_keys)
            )
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.list_objects(
                bucket, prefix, max_keys, continuation_token, delimiter, fetch_owner
            )
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_list_ttl)
            return result

    def head_object(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "cached_s3.head_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ) as span:
            cache_key = self._key("head_object", bucket, key)
            cached = self._cache.get_sync(cache_key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.head_object(bucket, key)
            self._cache.set_sync(cache_key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    def get_bucket_versioning(self, bucket: str) -> dict:
        with tracer.start_as_current_span(
            "cached_s3.get_bucket_versioning",
            attributes={"s3.bucket": bucket},
        ) as span:
            key = self._key("versioning", bucket)
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.get_bucket_versioning(bucket)
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    def get_bucket_acl(self, bucket: str) -> dict:
        with tracer.start_as_current_span(
            "cached_s3.get_bucket_acl",
            attributes={"s3.bucket": bucket},
        ) as span:
            key = self._key("bucket_acl", bucket)
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.get_bucket_acl(bucket)
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    def get_object_acl(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "cached_s3.get_object_acl",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ) as span:
            cache_key = self._key("object_acl", bucket, key)
            cached = self._cache.get_sync(cache_key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = self._inner.get_object_acl(bucket, key)
            self._cache.set_sync(cache_key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    # ── Uncached reads (streams / large results) ──────────────────────

    def get_object(self, bucket: str, key: str, version_id: str | None = None) -> dict:
        return self._inner.get_object(bucket, key, version_id)

    def list_object_versions(
        self,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
        key_marker: str | None = None,
        version_id_marker: str | None = None,
    ) -> dict:
        return self._inner.list_object_versions(
            bucket, prefix, max_keys, key_marker, version_id_marker
        )

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        return self._inner.generate_presigned_url(bucket, key, expires_in, method)

    # ── Write operations: delegate + invalidate ────────────────────────

    def _invalidate_bucket(self, name: str) -> None:
        """Invalidate all cached data for a specific bucket."""
        self._cache.delete_sync(self._key("list_buckets"))
        self._cache.delete_sync(self._key("head_bucket", name))
        self._cache.delete_sync(self._key("versioning", name))
        self._cache.delete_sync(self._key("bucket_acl", name))
        self._cache.invalidate_pattern_sync(self._key("list_objects", name, "*"))
        self._cache.invalidate_pattern_sync(self._key("head_object", name, "*"))
        self._cache.invalidate_pattern_sync(self._key("object_acl", name, "*"))

    def create_bucket(self, name: str) -> dict:
        result = self._inner.create_bucket(name)
        self._invalidate_bucket(name)
        return result

    def delete_bucket(self, name: str) -> dict:
        result = self._inner.delete_bucket(name)
        self._invalidate_bucket(name)
        return result

    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None:
        self._inner.put_object(bucket, key, body)
        self._cache.invalidate_pattern_sync(self._key("list_objects", bucket, "*"))
        self._cache.delete_sync(self._key("head_object", bucket, key))

    def delete_object(
        self, bucket: str, key: str, version_id: str | None = None
    ) -> dict:
        result = self._inner.delete_object(bucket, key, version_id)
        self._cache.invalidate_pattern_sync(self._key("list_objects", bucket, "*"))
        self._cache.delete_sync(self._key("head_object", bucket, key))
        self._cache.delete_sync(self._key("object_acl", bucket, key))
        return result

    def delete_objects(self, bucket: str, keys: list[str]) -> dict:
        result = self._inner.delete_objects(bucket, keys)
        self._cache.invalidate_pattern_sync(self._key("list_objects", bucket, "*"))
        for k in keys:
            self._cache.delete_sync(self._key("head_object", bucket, k))
            self._cache.delete_sync(self._key("object_acl", bucket, k))
        return result

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dst_bucket: str,
        dst_key: str,
    ) -> dict:
        result = self._inner.copy_object(src_bucket, src_key, dst_bucket, dst_key)
        self._cache.invalidate_pattern_sync(self._key("list_objects", dst_bucket, "*"))
        self._cache.delete_sync(self._key("head_object", dst_bucket, dst_key))
        self._cache.delete_sync(self._key("object_acl", dst_bucket, dst_key))
        return result

    def put_bucket_versioning(self, bucket: str, status: str) -> dict:
        result = self._inner.put_bucket_versioning(bucket, status)
        self._cache.delete_sync(self._key("versioning", bucket))
        return result

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict:
        result = self._inner.put_bucket_acl(bucket, acl)
        self._cache.delete_sync(self._key("bucket_acl", bucket))
        return result

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict:
        result = self._inner.put_object_acl(bucket, key, acl)
        self._cache.delete_sync(self._key("object_acl", bucket, key))
        return result

    # ── Multipart uploads (pass-through, no caching) ──────────────────

    def create_multipart_upload(self, bucket: str, key: str) -> dict:
        return self._inner.create_multipart_upload(bucket, key)

    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: IO[bytes],
    ) -> dict:
        return self._inner.upload_part(bucket, key, upload_id, part_number, body)

    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: list[dict],
    ) -> dict:
        result = self._inner.complete_multipart_upload(bucket, key, upload_id, parts)
        self._cache.invalidate_pattern_sync(self._key("list_objects", bucket, "*"))
        self._cache.delete_sync(self._key("head_object", bucket, key))
        return result

    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> dict:
        return self._inner.abort_multipart_upload(bucket, key, upload_id)

    def list_parts(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        max_parts: int = 1000,
    ) -> dict:
        return self._inner.list_parts(bucket, key, upload_id, max_parts)
