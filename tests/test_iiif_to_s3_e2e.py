"""End-to-end test of the rahcp IIIF -> S3 streaming pipeline against a real moto S3.

Exercises the `rahcp iiif upload` core in one process, over real HTTP:

    IIIF manifest + images          (real local http.server)
      -> rahcp_iiif.download_batches(sink=...)
      -> client.s3.upload(bytes)    (presign + retrying PUT)
      -> real HTTP PUT to the presigned URL -> moto S3 (ThreadedMotoServer)

and asserts the bytes actually land in the bucket and the tracker records them.

Everything is real HTTP (no transport patching): one stdlib ``http.server`` stands
in for the IIIF server and the HCP ``/auth/token`` + ``/presign`` endpoints, while
moto provides a genuine S3. Skip-existing, validation, verification and batched
presigning are NOT reimplemented here — those live in the bulk engine
(``s3 upload-all`` / ``s3 verify``); the backend storage path is covered against
moto in ``backend/tests/s3/test_moto_server_e2e.py``.
"""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import boto3
import pytest
from botocore.config import Config
from moto.server import ThreadedMotoServer

from rahcp_client import HCPClient
from rahcp_iiif import download_batches
from rahcp_tracker import SqliteTracker

pytestmark = pytest.mark.asyncio

BUCKET = "iiif-e2e"
REGION = "us-east-1"
BATCH = "C0074667"
IMAGE_BYTES = b"\xff\xd8e2e-jpeg-bytes\xff\xd9"

# Manifest with 3 canvases. get_image_ids() takes split("!")[1][:14].upper().
MANIFEST = {
    "items": [{"id": f"https://x/arkis!{BATCH}_0000{i}/canvas"} for i in range(1, 4)]
}
EXPECTED_KEYS = [f"{BATCH}/{BATCH}_0000{i}.jpg" for i in range(1, 4)]


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
    yield f"http://{host}:{port}"
    server.stop()


@pytest.fixture
def s3_client(moto_server: str):
    """Sync boto3 client used to presign (in the server) and to verify uploads."""
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
    """Local HTTP server: IIIF (manifest + images) + HCP /auth/token + /presign."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # keep test output clean
            pass

        def _send(self, status: int, body: bytes, ctype: str = "application/json"):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.endswith("/manifest"):
                self._send(200, json.dumps(MANIFEST).encode())
            elif self.path.endswith("default.jpg"):
                self._send(200, IMAGE_BYTES, "image/jpeg")
            else:  # pragma: no cover
                self._send(404, b"{}")

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            if self.path.endswith("/auth/token"):  # form-encoded body — not JSON
                self._send(
                    200,
                    json.dumps(
                        {"access_token": "test-token", "token_type": "bearer"}
                    ).encode(),
                )
            elif self.path.endswith("/presign"):
                req = json.loads(raw)
                url = s3_client.generate_presigned_url(
                    ClientMethod=req["method"],
                    Params={"Bucket": req["bucket"], "Key": req["key"]},
                    ExpiresIn=req.get("expires_in", 3600),
                )
                self._send(
                    200,
                    json.dumps(
                        {"url": url, "bucket": req["bucket"], "key": req["key"]}
                    ).encode(),
                )
            else:  # pragma: no cover
                self._send(404, b"{}")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


async def test_iiif_pipeline_streams_into_moto_s3(s3_client, fake_hcp, tmp_path):
    tracker = SqliteTracker(tmp_path / "e2e.db")

    async with HCPClient(
        endpoint=f"{fake_hcp}/api/v1", username="u", password="p", verify_ssl=False
    ) as client:

        async def sink(key: str, data: bytes) -> None:
            await client.s3.upload(BUCKET, key, data)

        stats = await download_batches(
            [BATCH], None, tracker, base_url=fake_hcp, workers=3, sink=sink
        )

    assert stats.ok == 3
    assert stats.errors == 0
    for key in EXPECTED_KEYS:
        assert (
            s3_client.get_object(Bucket=BUCKET, Key=key)["Body"].read() == IMAGE_BYTES
        )
    assert tracker.summary()["done"] == 3
    tracker.close()
