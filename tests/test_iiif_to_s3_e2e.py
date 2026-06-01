"""End-to-end test of the streaming IIIF -> S3 path against a real moto S3.

Drives ``rahcp_client.bulk.bulk_stream_upload`` (what ``rahcp iiif upload`` uses)
over real HTTP: bytes are fetched from a local IIIF stand-in and pushed through
the shared bulk engine to a ThreadedMotoServer S3, exercising batched presign,
skip-existing (HEAD), byte validation, verify, and the tracker.

One stdlib ``http.server`` stands in for the IIIF image server and the HCP
``/auth/token`` + bulk-``/objects/presign`` + ``HEAD /objects/{key}`` endpoints;
moto provides a genuine S3. The backend's own storage path is covered against
moto in ``backend/tests/s3/test_moto_server_e2e.py``.
"""

from __future__ import annotations

import io
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import boto3
import httpx
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from moto.server import ThreadedMotoServer
from PIL import Image

from rahcp_client import BulkStreamConfig, HCPClient, bulk_stream_upload
from rahcp_iiif.manifest import fetch_with_retry
from rahcp_tracker import SqliteTracker
from rahcp_validate import validate_bytes_by_extension

pytestmark = pytest.mark.asyncio

BUCKET = "iiif-e2e"
REGION = "us-east-1"
BATCH = "C0074667"


def _real_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buf, "JPEG")
    return buf.getvalue()


IMAGE_BYTES = _real_jpeg()  # genuinely decodable JPEG (passes byte validation)
KEYS = [f"{BATCH}/{BATCH}_0000{i}.jpg" for i in range(1, 4)]


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture
def moto_server():
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=_free_port())
    server.start()
    host, port = server.get_host_and_port()
    base = f"http://{host}:{port}"
    # moto's in-memory backends are process-global, so wipe any state left by a
    # prior test before this one creates its bucket.
    httpx.post(f"{base}/moto-api/reset")
    yield base
    server.stop()


@pytest.fixture
def s3_client(moto_server: str):
    client = boto3.client(
        "s3",
        endpoint_url=moto_server,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        region_name=REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    client.create_bucket(Bucket=BUCKET)
    return client


@pytest.fixture
def fake_hcp(s3_client):
    """IIIF image server + HCP auth / bulk-presign / HEAD, all backed by moto.

    ``bad_keys`` (mutable) makes the image endpoint serve corrupt bytes for those
    keys, so byte-validation can be exercised.
    """
    bad_keys: set[str] = set()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send(self, status, body=b"", ctype="application/json", headers=None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self):
            # IIIF image: /img/<key>  (test builds the URL, so any path with /img/)
            if "/img/" in self.path:
                key = urlparse(self.path).path.split("/img/", 1)[1]
                body = b"corrupt!" if key in bad_keys else IMAGE_BYTES
                self._send(200, body, "image/jpeg")
            else:  # pragma: no cover
                self._send(404, b"{}")

        def do_HEAD(self):
            # HEAD /api/v1/buckets/<bucket>/objects/<key> — skip-existing / verify.
            path = urlparse(self.path).path
            bucket = path.split("/buckets/")[1].split("/objects/")[0]
            key = path.split("/objects/", 1)[1]
            try:
                meta = s3_client.head_object(Bucket=bucket, Key=key)
            except ClientError:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", str(meta["ContentLength"]))
            self.end_headers()

        def do_POST(self):
            path = urlparse(self.path).path
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            if path.endswith("/auth/token"):
                self._send(
                    200,
                    json.dumps(
                        {"access_token": "test-token", "token_type": "bearer"}
                    ).encode(),
                )
                return
            body = json.loads(raw) if raw else {}
            if path.endswith("/objects/presign"):  # bulk presign
                bucket = path.split("/buckets/")[1].split("/objects")[0]
                urls = [
                    {
                        "key": k,
                        "url": s3_client.generate_presigned_url(
                            ClientMethod=body["method"],
                            Params={"Bucket": bucket, "Key": k},
                            ExpiresIn=body.get("expires_in", 3600),
                        ),
                    }
                    for k in body["keys"]
                ]
                self._send(200, json.dumps({"urls": urls}).encode())
            else:  # pragma: no cover
                self._send(404, b"{}")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}", bad_keys
    server.shutdown()


def _items(base_url: str) -> list[tuple[str, str]]:
    # (s3_key, image_url) — image_url carries the key so the shim/bad_keys can match.
    return [(key, f"{base_url}/img/{key}") for key in KEYS]


async def _stream(base_url, client, tracker, *, validate=False, verify=False):
    async with httpx.AsyncClient(timeout=30) as http:

        async def fetch(url: str) -> bytes:
            resp = await fetch_with_retry(http, url)
            return resp.content

        return await bulk_stream_upload(
            BulkStreamConfig(
                client=client,
                bucket=BUCKET,
                tracker=tracker,
                workers=3,
                validate_bytes=validate_bytes_by_extension if validate else None,
                verify_upload=verify,
            ),
            _items(base_url),
            fetch,
        )


async def test_stream_upload_lands_in_moto_and_counts_match(
    s3_client, fake_hcp, tmp_path
):
    base_url, _bad = fake_hcp
    tracker = SqliteTracker(tmp_path / "e2e.db")
    async with HCPClient(
        endpoint=f"{base_url}/api/v1", username="u", password="p", verify_ssl=False
    ) as client:
        stats = await _stream(base_url, client, tracker, validate=True, verify=True)

    assert stats.ok == len(KEYS)
    assert stats.errors == 0
    for key in KEYS:
        assert (
            s3_client.get_object(Bucket=BUCKET, Key=key)["Body"].read() == IMAGE_BYTES
        )
    assert tracker.summary()["done"] == len(KEYS)
    tracker.close()


async def test_skip_existing_skips_already_uploaded(s3_client, fake_hcp, tmp_path):
    base_url, _bad = fake_hcp
    async with HCPClient(
        endpoint=f"{base_url}/api/v1", username="u", password="p", verify_ssl=False
    ) as client:
        first = await _stream(base_url, client, SqliteTracker(tmp_path / "a.db"))
        assert first.ok == len(KEYS)
        # Fresh tracker — must skip via HEAD (objects already in the bucket), not re-upload.
        second = await _stream(base_url, client, SqliteTracker(tmp_path / "b.db"))

    assert second.ok == 0
    assert second.skipped == len(KEYS)


async def test_validation_rejects_corrupt_image(s3_client, fake_hcp, tmp_path):
    base_url, bad = fake_hcp
    bad.add(KEYS[1])  # serve corrupt bytes for the 2nd image
    tracker = SqliteTracker(tmp_path / "e2e.db")
    async with HCPClient(
        endpoint=f"{base_url}/api/v1", username="u", password="p", verify_ssl=False
    ) as client:
        stats = await _stream(base_url, client, tracker, validate=True)

    assert stats.ok == len(KEYS) - 1
    assert stats.errors == 1
    # The corrupt one must NOT have been uploaded.
    with pytest.raises(ClientError):
        s3_client.head_object(Bucket=BUCKET, Key=KEYS[1])
    # ...and the failure is recorded with a phase-labeled reason.
    details = {key: reason for key, _size, reason in tracker.error_details()}
    assert KEYS[1] in details
    assert (details[KEYS[1]] or "").startswith("validate:")
    tracker.close()
