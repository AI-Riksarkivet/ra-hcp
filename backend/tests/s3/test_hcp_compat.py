"""HCP <10 → 10.0.x S3 compatibility probe.

The HCP adapter (``app/services/storage/adapters/hcp.py``) carries four
workarounds that were required for HCP **< 10** with modern aioboto3/botocore:

  1. ``request_checksum_calculation="when_required"`` + ``response_checksum_validation``
     — HCP < 10 rejected the AWS-SDK-2.23+ default CRC32 checksum headers (HCP-50739).
  2. ``s3={"addressing_style": "path"}`` — HCP < 10 had no virtual-host buckets (HCP-50750).
  3. ``client.meta.events.unregister("needs-retry.s3")`` — HCP returned non-standard
     redirects that crashed boto3's region redirector (not in the 10.0.1 notes).
  4. ``delete_objects`` looped per-key instead of the batch ``DeleteObjects`` API
     — HCP wanted Content-MD5 but boto3 sends CRC32 (ties to HCP-50739).

Each test below runs the relevant **server-side** operation with ONE workaround
DISABLED, directly against the live HCP S3 endpoint. A PASS means HCP now accepts
the default behaviour → that workaround can be removed.

Run it (creds auto-loaded from ../.rahcp/config.yaml, or via env vars):

    cd backend
    uv run --with pyyaml pytest -m hcp -v -s

Env overrides: HCP_S3_ENDPOINT, HCP_USERNAME, HCP_PASSWORD, HCP_TENANT,
HCP_TEST_BUCKET (default 'ra-compat-test'). Writes go ONLY to that bucket under a
unique ``_compat/<uuid>/`` prefix and are deleted in teardown.
"""

from __future__ import annotations

import os
import socket
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

import aioboto3
import pytest
from aiobotocore.config import AioConfig

from app.core.auth_utils import derive_s3_keys

pytestmark = pytest.mark.hcp


# ── Config resolution: env vars first, else ../.rahcp/config.yaml ──────────────


def _load_rahcp_profile() -> dict | None:
    """Best-effort load of the active rahcp profile (username/password/tenant)."""
    cfg_path = Path(__file__).resolve().parents[3] / ".rahcp" / "config.yaml"
    if not cfg_path.exists():
        return None
    try:
        import yaml  # optional; only needed for local credential autoload
    except ImportError:
        return None
    data = yaml.safe_load(cfg_path.read_text())
    return data["profiles"][data.get("default", "dev")]


_profile = _load_rahcp_profile() or {}

HCP_USERNAME = os.environ.get("HCP_USERNAME") or _profile.get("username", "")
HCP_PASSWORD = os.environ.get("HCP_PASSWORD") or _profile.get("password", "")
HCP_TENANT = os.environ.get("HCP_TENANT") or _profile.get("tenant", "dev-ai")
HCP_S3_ENDPOINT = os.environ.get("HCP_S3_ENDPOINT", f"https://{HCP_TENANT}.hcp.ra-dev.int")
HCP_TEST_BUCKET = os.environ.get("HCP_TEST_BUCKET", "ra-compat-test")
_CONNECT_TIMEOUT = int(os.environ.get("HCP_CONNECT_TIMEOUT", "10"))

if not (HCP_USERNAME and HCP_PASSWORD):
    pytest.skip("HCP credentials not configured (env or .rahcp)", allow_module_level=True)


def _hcp_is_reachable() -> bool:
    parsed = urlparse(HCP_S3_ENDPOINT)
    host = parsed.hostname or ""
    port = parsed.port or 443
    deadline = time.monotonic() + _CONNECT_TIMEOUT
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


if not _hcp_is_reachable():
    pytest.skip(
        f"HCP S3 endpoint {HCP_S3_ENDPOINT} not reachable — skipping",
        allow_module_level=True,
    )

_ACCESS_KEY, _SECRET_KEY = derive_s3_keys(HCP_USERNAME, HCP_PASSWORD)


@asynccontextmanager
async def hcp_client(
    *,
    addressing: str = "path",
    checksums: str | None = "when_required",
    drop_redirector: bool = True,
) -> AsyncGenerator:
    """Raw aioboto3 S3 client against live HCP, with each workaround individually toggleable.

    Defaults reproduce the production HcpStorage config. Override a kwarg to DISABLE
    that workaround:
      - addressing="virtual"        -> test HCP-50750 (virtual-host buckets)
      - checksums="when_supported"  -> test HCP-50739 (default CRC32 checksums)
      - drop_redirector=False       -> test the region-redirector workaround
    """
    kwargs: dict = {
        "signature_version": "s3v4",
        "s3": {"addressing_style": addressing},
        "retries": {"max_attempts": 1, "mode": "standard"},
        "connect_timeout": 10,
        "read_timeout": 60,
    }
    if checksums is not None:
        kwargs["request_checksum_calculation"] = checksums
        kwargs["response_checksum_validation"] = checksums
    session = aioboto3.Session(
        aws_access_key_id=_ACCESS_KEY, aws_secret_access_key=_SECRET_KEY
    )
    async with session.client(
        "s3",
        endpoint_url=HCP_S3_ENDPOINT,
        region_name="us-east-1",
        verify=False,
        config=AioConfig(**kwargs),
    ) as client:
        if drop_redirector:
            client.meta.events.unregister("needs-retry.s3")
        yield client


@pytest.fixture
async def prefix() -> AsyncGenerator[str]:
    """Unique key prefix inside the shared test bucket; deletes its keys on teardown."""
    p = f"_compat/{uuid.uuid4().hex}/"
    yield p
    async with hcp_client() as c:
        try:
            resp = await c.list_objects_v2(Bucket=HCP_TEST_BUCKET, Prefix=p)
            for obj in resp.get("Contents", []):
                await c.delete_object(Bucket=HCP_TEST_BUCKET, Key=obj["Key"])
        except Exception:
            pass


# ── Version (attribute every result to the exact HCP build) ───────────────────


async def test_report_hcp_response_headers():
    """Dump HCP S3 response headers so results are attributed to the real endpoint.

    HCP's S3 gateway does not return a Server/version header, so version is recorded
    out-of-band (operator-confirmed 10.0.0). This just proves the endpoint answers and
    surfaces whatever identifying headers it does send.
    """
    async with hcp_client() as c:
        resp = await c.list_buckets()
    headers = resp["ResponseMetadata"]["HTTPHeaders"]
    print(f"\n[HCP] {HCP_S3_ENDPOINT} response headers:")
    for k in sorted(headers):
        print(f"        {k}: {headers[k]}")
    assert headers, "HCP returned no response headers"


# ── (1)+(4) Checksums: HCP-50739 ──────────────────────────────────────────────


async def test_default_crc32_checksum_single_put_accepted(prefix: str):
    """put_object (<8MB single PUT) with SDK-default CRC32 checksums. PASS => workaround removable."""
    key = f"{prefix}small.txt"
    body = b"hello hcp checksum default " * 100  # ~2.7 KB
    async with hcp_client(checksums="when_supported") as c:
        await c.put_object(Bucket=HCP_TEST_BUCKET, Key=key, Body=body)
        got = await c.get_object(Bucket=HCP_TEST_BUCKET, Key=key)
        assert await got["Body"].read() == body


async def test_default_crc32_checksum_multipart_accepted(prefix: str):
    """SDK multipart upload (>=8MB via upload_fileobj) with default checksums. PASS => removable."""
    import io

    key = f"{prefix}large.bin"
    body = b"M" * (9 * 1024 * 1024)  # 9 MB -> crosses 8MB multipart threshold
    async with hcp_client(checksums="when_supported") as c:
        await c.upload_fileobj(io.BytesIO(body), HCP_TEST_BUCKET, key)
        head = await c.head_object(Bucket=HCP_TEST_BUCKET, Key=key)
        assert head["ContentLength"] == len(body)


async def test_batch_delete_still_requires_content_md5(prefix: str):
    """Native batch DeleteObjects STILL fails on HCP 10.0.0 — it demands Content-MD5,
    but modern boto3 sends CRC32. This proves the per-key delete loop (hcp.py:113-132)
    must be KEPT. If HCP ever fixes this, this test flips red → loop can be removed.
    """
    from botocore.exceptions import ClientError

    keys = [f"{prefix}batch-{i}.txt" for i in range(3)]
    async with hcp_client(checksums="when_supported") as c:
        for k in keys:
            await c.put_object(Bucket=HCP_TEST_BUCKET, Key=k, Body=b"x")
        with pytest.raises(ClientError, match="Content-MD5"):
            await c.delete_objects(
                Bucket=HCP_TEST_BUCKET,
                Delete={"Objects": [{"Key": k} for k in keys], "Quiet": True},
            )


# ── (2) Virtual-host addressing: HCP-50750 ────────────────────────────────────


async def test_virtual_host_addressing_accepted(prefix: str):
    """Virtual-host addressing (bucket as subdomain). PASS => path-style no longer required.

    Skips (rather than fails) if the bucket subdomain doesn't resolve from here — that
    is a DNS/cert limitation of the test host, not an HCP rejection.
    """
    from botocore.exceptions import EndpointConnectionError

    key = f"{prefix}virtual.txt"
    try:
        async with hcp_client(addressing="virtual") as c:
            await c.put_object(Bucket=HCP_TEST_BUCKET, Key=key, Body=b"virtual")
            got = await c.get_object(Bucket=HCP_TEST_BUCKET, Key=key)
            assert await got["Body"].read() == b"virtual"
    except EndpointConnectionError as exc:
        pytest.skip(f"virtual-host subdomain not resolvable from here: {exc}")


# ── (3) Region redirector ─────────────────────────────────────────────────────


async def test_list_buckets_without_redirector_unregister():
    """list_buckets WITHOUT unregistering the region redirector. PASS => unregister removable."""
    async with hcp_client(drop_redirector=False) as c:
        resp = await c.list_buckets()
        assert "Buckets" in resp
