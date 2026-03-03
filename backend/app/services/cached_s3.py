"""Cached S3 service — wraps S3Service with sync Redis caching.

Uses composition (not inheritance) because S3Service methods are sync
and called via asyncio.to_thread(). The sync Redis client in CacheService
is safe to use from these threads.
"""

from __future__ import annotations

import logging
from typing import IO, List, Optional

from opentelemetry import trace

from app.core.config import CacheSettings, S3Settings
from app.services.cache_service import CacheService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CachedS3Service(S3Service):
    """S3Service with transparent Redis caching on metadata reads.

    Inherits from S3Service so that ``isinstance`` checks and DI type
    hints continue to work. Overrides individual methods to add caching.
    """

    def __init__(
        self,
        settings: S3Settings,
        cache: CacheService,
        cache_settings: CacheSettings,
    ):
        super().__init__(settings)
        self._cache = cache
        self._cs = cache_settings

    @classmethod
    def with_credentials(
        cls,
        settings: S3Settings,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
        *,
        cache: CacheService,
        cache_settings: CacheSettings,
    ) -> "CachedS3Service":
        """Create a CachedS3Service with explicit credentials + cache."""
        instance: CachedS3Service = super().with_credentials(  # type: ignore[assignment]
            settings, access_key, secret_key, endpoint_url=endpoint_url
        )
        instance._cache = cache
        instance._cs = cache_settings
        return instance

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
            result = super().list_buckets()
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_list_ttl)
            return result

    def head_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "cached_s3.head_bucket",
            attributes={"s3.bucket": name},
        ) as span:
            key = self._key("head_bucket", name)
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = super().head_bucket(name)
            self._cache.set_sync(key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> dict:
        # Only cache the first page (no continuation token)
        if continuation_token is not None:
            return super().list_objects(bucket, prefix, max_keys, continuation_token)
        with tracer.start_as_current_span(
            "cached_s3.list_objects",
            attributes={"s3.bucket": bucket, "s3.prefix": prefix or ""},
        ) as span:
            key = self._key("list_objects", bucket, prefix or "")
            cached = self._cache.get_sync(key)
            if cached is not None:
                span.set_attribute("cache.hit", True)
                return cached
            span.set_attribute("cache.hit", False)
            result = super().list_objects(bucket, prefix, max_keys, continuation_token)
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
            result = super().head_object(bucket, key)
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
            result = super().get_bucket_versioning(bucket)
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
            result = super().get_bucket_acl(bucket)
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
            result = super().get_object_acl(bucket, key)
            self._cache.set_sync(cache_key, result, ttl=self._cs.cache_s3_meta_ttl)
            return result

    # ── get_object is NEVER cached (body streams) ──────────────────────

    # ── Write operations: delegate + invalidate ────────────────────────

    def create_bucket(self, name: str) -> dict:
        result = super().create_bucket(name)
        self._cache.delete_sync(self._key("list_buckets"))
        self._cache.invalidate_pattern_sync(f"s3:*:{name}*")
        return result

    def delete_bucket(self, name: str) -> dict:
        result = super().delete_bucket(name)
        self._cache.delete_sync(self._key("list_buckets"))
        self._cache.invalidate_pattern_sync(f"s3:*:{name}*")
        return result

    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None:
        super().put_object(bucket, key, body)
        self._cache.invalidate_pattern_sync(f"s3:list_objects:{bucket}:*")
        self._cache.delete_sync(self._key("head_object", bucket, key))

    def delete_object(self, bucket: str, key: str) -> dict:
        result = super().delete_object(bucket, key)
        self._cache.invalidate_pattern_sync(f"s3:list_objects:{bucket}:*")
        self._cache.delete_sync(self._key("head_object", bucket, key))
        self._cache.delete_sync(self._key("object_acl", bucket, key))
        return result

    def delete_objects(self, bucket: str, keys: List[str]) -> dict:
        result = super().delete_objects(bucket, keys)
        self._cache.invalidate_pattern_sync(f"s3:list_objects:{bucket}:*")
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
        result = super().copy_object(src_bucket, src_key, dst_bucket, dst_key)
        self._cache.invalidate_pattern_sync(f"s3:list_objects:{dst_bucket}:*")
        return result

    def put_bucket_versioning(self, bucket: str, status: str) -> dict:
        result = super().put_bucket_versioning(bucket, status)
        self._cache.delete_sync(self._key("versioning", bucket))
        return result

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict:
        result = super().put_bucket_acl(bucket, acl)
        self._cache.delete_sync(self._key("bucket_acl", bucket))
        return result

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict:
        result = super().put_object_acl(bucket, key, acl)
        self._cache.delete_sync(self._key("object_acl", bucket, key))
        return result
