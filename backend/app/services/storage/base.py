"""Abstract base class for storage adapters.

StorageBase provides:
  - @abstractmethod for every required operation (enforced at instantiation)
  - Shared default implementations where the logic is backend-agnostic
    (e.g. delete_objects as a loop of delete_object)

Adapters inherit from StorageBase and override the abstract methods.
Endpoint code type-hints against StorageProtocol (structural typing).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import IO, List, Optional


class StorageBase(ABC):
    """Base class for all storage backend adapters."""

    # ── Bucket operations ──────────────────────────────────────────────

    @abstractmethod
    def list_buckets(self) -> dict: ...

    @abstractmethod
    def create_bucket(self, name: str) -> dict: ...

    @abstractmethod
    def head_bucket(self, name: str) -> dict: ...

    @abstractmethod
    def delete_bucket(self, name: str) -> dict: ...

    # ── Object operations ──────────────────────────────────────────────

    @abstractmethod
    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
        delimiter: Optional[str] = None,
        fetch_owner: bool = True,
    ) -> dict: ...

    @abstractmethod
    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None: ...

    @abstractmethod
    def get_object(self, bucket: str, key: str) -> dict: ...

    @abstractmethod
    def head_object(self, bucket: str, key: str) -> dict: ...

    @abstractmethod
    def delete_object(self, bucket: str, key: str) -> dict: ...

    def delete_objects(self, bucket: str, keys: List[str]) -> dict:
        """Delete multiple objects — default loops over delete_object.

        Backends that support efficient batch deletes should override this.
        """
        errors: list[dict] = []
        for key in keys:
            try:
                self.delete_object(bucket, key)
            except Exception as exc:
                errors.append({"Key": key, "Code": "DeleteError", "Message": str(exc)})
        return {"Errors": errors} if errors else {}

    @abstractmethod
    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dst_bucket: str,
        dst_key: str,
    ) -> dict: ...

    # ── Bucket versioning ─────────────────────────────────────────────

    @abstractmethod
    def get_bucket_versioning(self, bucket: str) -> dict: ...

    @abstractmethod
    def put_bucket_versioning(self, bucket: str, status: str) -> dict: ...

    # ── ACLs ──────────────────────────────────────────────────────────

    @abstractmethod
    def get_bucket_acl(self, bucket: str) -> dict: ...

    @abstractmethod
    def put_bucket_acl(self, bucket: str, acl: dict) -> dict: ...

    @abstractmethod
    def get_object_acl(self, bucket: str, key: str) -> dict: ...

    @abstractmethod
    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict: ...

    # ── Object versions ────────────────────────────────────────────

    @abstractmethod
    def list_object_versions(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        key_marker: Optional[str] = None,
        version_id_marker: Optional[str] = None,
    ) -> dict: ...

    # ── Presigned URLs ───────────────────────────────────────────────

    @abstractmethod
    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str: ...

    # ── Multipart uploads ────────────────────────────────────────────

    @abstractmethod
    def create_multipart_upload(self, bucket: str, key: str) -> dict: ...

    @abstractmethod
    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: IO[bytes],
    ) -> dict: ...

    @abstractmethod
    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[dict],
    ) -> dict: ...

    @abstractmethod
    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> dict: ...

    @abstractmethod
    def list_parts(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        max_parts: int = 1000,
    ) -> dict: ...
