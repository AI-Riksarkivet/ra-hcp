"""HCP storage adapter — boto3 wrapper with HCP-specific workarounds.

This is the original S3Service moved into the storage adapter structure.
HCP-specific quirks:
  - Region redirector disabled (HCP returns non-standard redirects)
  - Multi-delete uses individual deletes (HCP requires Content-MD5 but
    boto3 sends CRC32 for the batch delete API)
  - Path-style addressing (HCP doesn't support virtual-hosted buckets)
"""

from __future__ import annotations

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.client import BaseClient
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError
from opentelemetry import trace

from app.core.config import S3Settings
from app.services.storage.adapters._boto3_ops import Boto3Forwarder, Boto3Operations
from app.services.storage.errors import from_client_error, from_transport_error

tracer = trace.get_tracer(__name__)


class HcpStorage(Boto3Forwarder):
    """Synchronous boto3 wrapper for HCP — call methods via asyncio.to_thread().

    Implements StorageProtocol via composition: a Boto3Operations instance
    (``self._ops``) provides the shared S3 methods.  Boto3Forwarder supplies
    typed forwarding methods for protocol compliance.  Only HCP-specific
    overrides are defined here.
    """

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
    def _disable_region_redirector(client: BaseClient) -> None:
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
        self._ops = Boto3Operations(self._client, self._transfer_config)

    @classmethod
    def with_credentials(
        cls,
        settings: S3Settings,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
    ) -> HcpStorage:
        """Create an HcpStorage with explicit credentials (no env-var fallback)."""
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
        instance._ops = Boto3Operations(instance._client, instance._transfer_config)
        return instance

    # -- HCP-specific overrides ---------------------------------------------

    def list_buckets(self) -> dict:
        """Override: also catches TypeError from residual region redirector."""
        with tracer.start_as_current_span("s3.list_buckets"):
            try:
                return self._client.list_buckets()
            except ClientError as exc:
                raise from_client_error(exc) from exc
            except (BotoCoreError, TypeError) as exc:
                raise from_transport_error(exc) from exc

    def delete_objects(self, bucket: str, keys: list[str]) -> dict:
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
