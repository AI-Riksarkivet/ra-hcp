"""S3 data-plane service wrapping boto3 for HCP."""

from __future__ import annotations

from typing import IO, Any, Optional, List

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
from opentelemetry import trace

from app.core.config import S3Settings

tracer = trace.get_tracer(__name__)


class S3Service:
    """Synchronous boto3 wrapper — call methods via asyncio.to_thread()."""

    _BOTO_CONFIG = BotoConfig(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        retries={"max_attempts": 3, "mode": "adaptive"},
        connect_timeout=10,
        read_timeout=60,
    )

    @staticmethod
    def _disable_region_redirector(client: Any) -> None:
        """Unregister boto3's S3 region redirect handler.

        HCP is not AWS and returns non-standard responses that trigger
        boto3's S3RegionRedirectorv2.  On list_buckets (which has no
        bucket), the redirector calls head_bucket(Bucket=None) which
        crashes with TypeError.  Disabling it is safe for any non-AWS
        S3-compatible endpoint.
        """
        client.meta.events.unregister("needs-retry.s3")

    def __init__(self, settings: S3Settings):
        self.settings = settings
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.endpoint_url,
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
            region_name=settings.region,
            verify=settings.verify_ssl,
            config=self._BOTO_CONFIG,
        )
        self._disable_region_redirector(self._client)
        self._transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
        )

    @classmethod
    def with_credentials(
        cls,
        settings: S3Settings,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
        **kwargs: Any,
    ) -> S3Service:
        """Create an S3Service with explicit credentials (no env-var fallback)."""
        instance = cls.__new__(cls)
        instance.settings = settings
        instance._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or settings.endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.region,
            verify=settings.verify_ssl,
            config=cls._BOTO_CONFIG,
        )
        cls._disable_region_redirector(instance._client)
        instance._transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
        )
        return instance

    # ── Bucket operations ──────────────────────────────────────────────

    def list_buckets(self) -> dict:
        with tracer.start_as_current_span("s3.list_buckets"):
            return self._client.list_buckets()

    def create_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "s3.create_bucket", attributes={"s3.bucket": name}
        ):
            return self._client.create_bucket(Bucket=name)

    def head_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "s3.head_bucket", attributes={"s3.bucket": name}
        ):
            return self._client.head_bucket(Bucket=name)

    def delete_bucket(self, name: str) -> dict:
        with tracer.start_as_current_span(
            "s3.delete_bucket", attributes={"s3.bucket": name}
        ):
            return self._client.delete_bucket(Bucket=name)

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

    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None:
        with tracer.start_as_current_span(
            "s3.put_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            self._client.upload_fileobj(
                body,
                bucket,
                key,
                Config=self._transfer_config,
            )

    def get_object(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            return self._client.get_object(Bucket=bucket, Key=key)

    def head_object(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.head_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            return self._client.head_object(Bucket=bucket, Key=key)

    def delete_object(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.delete_object",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            return self._client.delete_object(Bucket=bucket, Key=key)

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
            return self._client.copy_object(
                CopySource={"Bucket": src_bucket, "Key": src_key},
                Bucket=dst_bucket,
                Key=dst_key,
            )

    def delete_objects(self, bucket: str, keys: List[str]) -> dict:
        """Delete multiple objects individually (HCP requires Content-MD5
        for the multi-delete API but boto3 sends CRC32 instead)."""
        with tracer.start_as_current_span(
            "s3.delete_objects",
            attributes={"s3.bucket": bucket, "s3.key_count": len(keys)},
        ):
            errors: list[dict] = []
            for key in keys:
                try:
                    self._client.delete_object(Bucket=bucket, Key=key)
                except ClientError as exc:
                    errors.append(
                        {
                            "Key": key,
                            "Code": exc.response["Error"].get("Code", "Unknown"),
                            "Message": exc.response["Error"].get("Message", ""),
                        }
                    )
            return {"Errors": errors} if errors else {}

    # ── Bucket versioning ─────────────────────────────────────────────

    def get_bucket_versioning(self, bucket: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_bucket_versioning",
            attributes={"s3.bucket": bucket},
        ):
            return self._client.get_bucket_versioning(Bucket=bucket)

    def put_bucket_versioning(self, bucket: str, status: str) -> dict:
        with tracer.start_as_current_span(
            "s3.put_bucket_versioning",
            attributes={"s3.bucket": bucket, "s3.versioning_status": status},
        ):
            return self._client.put_bucket_versioning(
                Bucket=bucket,
                VersioningConfiguration={"Status": status},
            )

    # ── ACLs ──────────────────────────────────────────────────────────

    def get_bucket_acl(self, bucket: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_bucket_acl",
            attributes={"s3.bucket": bucket},
        ):
            return self._client.get_bucket_acl(Bucket=bucket)

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict:
        with tracer.start_as_current_span(
            "s3.put_bucket_acl",
            attributes={"s3.bucket": bucket},
        ):
            return self._client.put_bucket_acl(
                Bucket=bucket,
                AccessControlPolicy=acl,
            )

    def get_object_acl(self, bucket: str, key: str) -> dict:
        with tracer.start_as_current_span(
            "s3.get_object_acl",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            return self._client.get_object_acl(Bucket=bucket, Key=key)

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict:
        with tracer.start_as_current_span(
            "s3.put_object_acl",
            attributes={"s3.bucket": bucket, "s3.key": key},
        ):
            return self._client.put_object_acl(
                Bucket=bucket,
                Key=key,
                AccessControlPolicy=acl,
            )

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
            return self._client.generate_presigned_url(
                method,
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=expires_in,
            )
