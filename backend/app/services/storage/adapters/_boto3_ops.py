"""Shared boto3 method implementations for S3-compatible storage adapters.

Boto3Operations is a standalone class that holds a boto3 client and
TransferConfig, providing the 21 S3 methods that are identical across
HcpStorage and GenericBoto3Storage.

Each concrete adapter composes a Boto3Operations instance via the
@delegates_to decorator, which generates thin forwarding methods so that:

  - Methods are statically discoverable (isinstance works with
    @runtime_checkable Protocol on Python 3.12+)
  - Override methods defined directly on the adapter take precedence

Overrides per adapter:
  - HcpStorage overrides list_buckets (catches TypeError) and
    delete_objects (individual deletes for HCP Content-MD5 bug)
  - GenericBoto3Storage overrides delete_objects (native batch) and
    4 ACL methods (raise NotSupported)
"""

from __future__ import annotations

from typing import IO, Any

from boto3.s3.transfer import TransferConfig
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from opentelemetry import trace

from app.services.storage.errors import from_client_error, from_transport_error

tracer = trace.get_tracer(__name__)


class Boto3Operations:
    """Shared boto3 S3 method implementations.

    Args:
        client: A boto3 S3 client.
        transfer_config: A boto3 TransferConfig for multipart uploads.
    """

    def __init__(self, client: BaseClient, transfer_config: TransferConfig) -> None:
        self._client = client
        self._transfer_config = transfer_config

    # -- Bucket operations --------------------------------------------------

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

    # -- Object operations --------------------------------------------------

    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
        continuation_token: str | None = None,
        delimiter: str | None = None,
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

    def get_object(self, bucket: str, key: str, version_id: str | None = None) -> dict:
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
        self, bucket: str, key: str, version_id: str | None = None
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

    # -- Bucket versioning --------------------------------------------------

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

    # -- ACLs ---------------------------------------------------------------

    def get_bucket_acl(self, bucket: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_bucket_acl",
            attributes={"s3.bucket": bucket},
        ):
            try:
                return self._client.get_bucket_acl(Bucket=bucket)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict:
        with tracer.start_as_current_span(
            "s3.put_bucket_acl",
            attributes={"s3.bucket": bucket},
        ):
            try:
                return self._client.put_bucket_acl(
                    Bucket=bucket,
                    AccessControlPolicy=acl,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def get_object_acl(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_object_acl",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.get_object_acl(Bucket=bucket, Key=key)
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict:
        with tracer.start_as_current_span(
            "s3.put_object_acl",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            try:
                return self._client.put_object_acl(
                    Bucket=bucket,
                    Key=key,
                    AccessControlPolicy=acl,
                )
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except BotoCoreError as exc:
                raise from_transport_error(exc) from exc

    # -- Object versions ----------------------------------------------------

    def list_object_versions(
        self,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
        key_marker: str | None = None,
        version_id_marker: str | None = None,
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

    # -- Presigned URLs -----------------------------------------------------

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

    # -- Multipart uploads --------------------------------------------------

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
        parts: list[dict],
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


def delegates_to(ops_attr: str, ops_cls: type):
    """Class decorator: generate forwarding methods for composition.

    For every public method on *ops_cls* that is not already defined on
    the decorated class, creates a thin forwarder that calls
    ``getattr(self.<ops_attr>, method_name)(*args, **kwargs)``.

    This makes delegated methods statically discoverable so that
    ``isinstance(obj, StorageProtocol)`` works on Python 3.12+
    (where ``@runtime_checkable`` uses ``inspect.getattr_static``).
    """

    def decorator(cls: type) -> type:
        for name, method in vars(ops_cls).items():
            if name.startswith("_") or not callable(method):
                continue
            if name in cls.__dict__:
                continue  # explicit override takes precedence

            def _make(n: str):
                def forwarder(self, *args, **kwargs):
                    return getattr(getattr(self, ops_attr), n)(*args, **kwargs)

                forwarder.__name__ = n
                forwarder.__qualname__ = f"{cls.__qualname__}.{n}"
                return forwarder

            setattr(cls, name, _make(name))
        return cls

    return decorator
