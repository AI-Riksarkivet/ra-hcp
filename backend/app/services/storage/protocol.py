"""Backend-agnostic storage protocol for S3-compatible services."""

from __future__ import annotations

from typing import IO, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class StorageProtocol(Protocol):
    """Interface that every storage backend must implement.

    All methods are synchronous — callers run them via asyncio.to_thread().
    Methods return plain dicts matching the boto3 response shapes so existing
    endpoint code works without changes.
    """

    # ── Bucket operations ──────────────────────────────────────────────

    def list_buckets(self) -> dict: ...

    def create_bucket(self, name: str) -> dict: ...

    def head_bucket(self, name: str) -> dict: ...

    def delete_bucket(self, name: str) -> dict: ...

    # ── Object operations ──────────────────────────────────────────────

    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
        delimiter: Optional[str] = None,
        fetch_owner: bool = True,
    ) -> dict: ...

    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None: ...

    def get_object(self, bucket: str, key: str) -> dict: ...

    def head_object(self, bucket: str, key: str) -> dict: ...

    def delete_object(self, bucket: str, key: str) -> dict: ...

    def delete_objects(self, bucket: str, keys: List[str]) -> dict: ...

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dst_bucket: str,
        dst_key: str,
    ) -> dict: ...

    # ── Bucket versioning ─────────────────────────────────────────────

    def get_bucket_versioning(self, bucket: str) -> dict: ...

    def put_bucket_versioning(self, bucket: str, status: str) -> dict: ...

    # ── ACLs ──────────────────────────────────────────────────────────

    def get_bucket_acl(self, bucket: str) -> dict: ...

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict: ...

    def get_object_acl(self, bucket: str, key: str) -> dict: ...

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict: ...

    # ── Presigned URLs ───────────────────────────────────────────────

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str: ...
