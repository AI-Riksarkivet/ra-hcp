"""Generic boto3 storage adapter for S3-compatible backends (MinIO, Ceph, AWS).

No HCP-specific workarounds:
  - Region redirector left intact (standard S3 behavior)
  - Native batch delete_objects (no Content-MD5 issue)
  - Configurable addressing style (path/virtual/auto)
  - ACL methods raise StorageOperationNotSupported (MinIO deprecated ACLs)
"""

from __future__ import annotations

import logging
from typing import IO, Any, List, Optional

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from opentelemetry import trace

from app.core.config import StorageSettings
from app.services.storage.base import StorageBase
from app.services.storage.errors import (
    StorageOperationNotSupported,
    from_client_error,
    from_transport_error,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class GenericBoto3Storage(StorageBase):
    """Standard boto3 S3 adapter — no vendor-specific hacks.

    Implements StorageProtocol via StorageBase. Call methods via
    asyncio.to_thread() from async endpoint code.
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

    # ── Bucket operations ──────────────────────────────────────────────

    def list_buckets(self) -> dict:
        with tracer.start_as_current_span("s3.list_buckets"):
            try:
                return self._client.list_buckets()
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def create_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "s3.create_bucket", attributes={"s3.bucket": name}
        ):
            try:
                return self._client.create_bucket(Bucket=name)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def head_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "s3.head_bucket", attributes={"s3.bucket": name}
        ):
            try:
                return self._client.head_bucket(Bucket=name)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def delete_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "s3.delete_bucket", attributes={"s3.bucket": name}
        ):
            try:
                return self._client.delete_bucket(Bucket=name)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    # ── Object operations ──────────────────────────────────────────────

    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
        delimiter: Optional[str] = None,
        fetch_owner: bool = True,
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.list_objects",
            attributes={"s3.bucket": bucket, "s3.prefix": prefix or ""},
        ):
            try:
                kwargs: dict[str, Any] = {"Bucket": bucket, "MaxKeys": max_keys}
                if prefix:
                    kwargs["Prefix"] = prefix
                if continuation_token:
                    kwargs["ContinuationToken"] = continuation_token
                if delimiter:
                    kwargs["Delimiter"] = delimiter
                if fetch_owner:
                    kwargs["FetchOwner"] = True
                return self._client.list_objects_v2(**kwargs)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None:
        with tracer.start_as_current_span(
            "s3.put_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                self._client.upload_fileobj(
                    body,
                    bucket,
                    key,
                    Config=self._transfer_config,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def get_object(
        self, bucket: str, key: str, version_id: Optional[str] = None
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.get_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                kwargs: dict[str, Any] = {"Bucket": bucket, "Key": key}
                if version_id:
                    kwargs["VersionId"] = version_id
                return self._client.get_object(**kwargs)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def head_object(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.head_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.head_object(Bucket=bucket, Key=key)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def delete_object(
        self, bucket: str, key: str, version_id: Optional[str] = None
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.delete_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                kwargs: dict[str, Any] = {"Bucket": bucket, "Key": key}
                if version_id:
                    kwargs["VersionId"] = version_id
                return self._client.delete_object(**kwargs)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dst_bucket: str,
        dst_key: str,
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.copy_object",
            attributes={
                "s3.bucket": dst_bucket,
                "s3.key": dst_key,
                "s3.source_bucket": src_bucket,
                "s3.source_key": src_key,
            },
        ):
            try:
                return self._client.copy_object(
                    CopySource={"Bucket": src_bucket, "Key": src_key},
                    Bucket=dst_bucket,
                    Key=dst_key,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

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

    # ── Bucket versioning ─────────────────────────────────────────────

    def get_bucket_versioning(self, bucket: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_bucket_versioning",
            attributes={"s3.bucket": bucket},
        ):
            try:
                return self._client.get_bucket_versioning(Bucket=bucket)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def put_bucket_versioning(self, bucket: str, status: str) -> dict:
        with tracer.start_as_current_span(
            "s3.put_bucket_versioning",
            attributes={"s3.bucket": bucket, "s3.versioning_status": status},
        ):
            try:
                return self._client.put_bucket_versioning(
                    Bucket=bucket,
                    VersioningConfiguration={"Status": status},
                )
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

    # ── Object versions ────────────────────────────────────────────

    def list_object_versions(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        key_marker: Optional[str] = None,
        version_id_marker: Optional[str] = None,
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.list_object_versions",
            attributes={"s3.bucket": bucket, "s3.prefix": prefix or ""},
        ):
            try:
                kwargs: dict[str, Any] = {"Bucket": bucket, "MaxKeys": max_keys}
                if prefix:
                    kwargs["Prefix"] = prefix
                if key_marker:
                    kwargs["KeyMarker"] = key_marker
                if version_id_marker:
                    kwargs["VersionIdMarker"] = version_id_marker
                return self._client.list_object_versions(**kwargs)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    # ── Presigned URLs ───────────────────────────────────────────────

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        with tracer.start_as_current_span(
            "s3.generate_presigned_url",
            attributes={"s3.bucket": bucket, "s3.key": key, "s3.method": method},
        ):
            try:
                return self._client.generate_presigned_url(
                    method,
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    # ── Multipart uploads ────────────────────────────────────────────

    def create_multipart_upload(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.create_multipart_upload",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.create_multipart_upload(Bucket=bucket, Key=key)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        body: IO[bytes],
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.upload_part",
            attributes={
                "s3.bucket": bucket,
                "s3.key": key,
                "s3.part_number": part_number,
            },
        ):
            try:
                return self._client.upload_part(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=body,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def complete_multipart_upload(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[dict],
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.complete_multipart_upload",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.complete_multipart_upload(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> dict:
        with tracer.start_as_current_span(
            "s3.abort_multipart_upload",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.abort_multipart_upload(
                    Bucket=bucket, Key=key, UploadId=upload_id
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def list_parts(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        max_parts: int = 1000,
    ) -> dict:
        with tracer.start_as_current_span(
            "s3.list_parts",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.list_parts(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id,
                    MaxParts=max_parts,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc
