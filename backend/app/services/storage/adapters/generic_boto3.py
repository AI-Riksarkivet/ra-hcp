"""Generic boto3 storage adapter for S3-compatible backends (MinIO, Ceph, AWS).

No HCP-specific workarounds:
  - Region redirector left intact (standard S3 behavior)
  - Native batch delete_objects (no Content-MD5 issue)
  - Configurable addressing style (path/virtual/auto)
  - ACL methods raise StorageOperationNotSupported (MinIO deprecated ACLs)
"""

from __future__ import annotations

import logging
from typing import Any, List

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from opentelemetry import trace

from app.core.config import StorageSettings
from app.services.storage.adapters._boto3_mixin import Boto3StorageMixin
from app.services.storage.base import StorageBase
from app.services.storage.errors import (
    StorageOperationNotSupported,
    from_client_error,
    from_transport_error,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class GenericBoto3Storage(Boto3StorageMixin, StorageBase):
    """Standard boto3 S3 adapter — no vendor-specific hacks.

    Implements StorageProtocol via StorageBase. Call methods via
    asyncio.to_thread() from async endpoint code.

    Common boto3 methods are inherited from Boto3StorageMixin.
    Only GenericBoto3-specific overrides are defined here.
    """

    def __init__(self, settings: StorageSettings):
        self.settings = settings
        boto_config = BotoConfig(
            signature_version="s3v4",
            s3={"addressing_style": settings.s3_addressing_style},
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=60,
        )
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
            verify=settings.s3_verify_ssl,
            config=boto_config,
        )
        self._transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
        )

    @classmethod
    def with_credentials(
        cls,
        settings: StorageSettings,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
        **kwargs: Any,
    ) -> GenericBoto3Storage:
        """Create a GenericBoto3Storage with explicit credentials."""
        instance = cls.__new__(cls)
        instance.settings = settings
        boto_config = BotoConfig(
            signature_version="s3v4",
            s3={"addressing_style": settings.s3_addressing_style},
            retries={"max_attempts": 3, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=60,
        )
        instance._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or settings.s3_endpoint_url or None,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.s3_region,
            verify=settings.s3_verify_ssl,
            config=boto_config,
        )
        instance._transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
        )
        return instance

    # ── GenericBoto3-specific overrides ────────────────────────────────

    def delete_objects(self, bucket: str, keys: List[str]) -> dict:
        """Native batch delete — works on standard S3-compatible backends."""
        with tracer.start_as_current_span(
            "s3.delete_objects",
            attributes={"s3.bucket": bucket, "s3.key_count": len(keys)},
        ):
            try:
                result = self._client.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
                )
                errors = result.get("Errors", [])
                return {"Errors": errors} if errors else {}
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    # ── ACLs (not supported on MinIO) ─────────────────────────────────

    def get_bucket_acl(self, bucket: str) -> dict:
        raise StorageOperationNotSupported("get_bucket_acl", "minio")

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict:
        raise StorageOperationNotSupported("put_bucket_acl", "minio")

    def get_object_acl(self, bucket: str, key: str) -> dict:
        raise StorageOperationNotSupported("get_object_acl", "minio")

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict:
        raise StorageOperationNotSupported("put_object_acl", "minio")
