"""End-to-end test of Transkribus export → streaming S3 upload against real moto S3.

Drives the ``rahcp transkribus upload`` path over real HTTP: a local stand-in
serves the Transkribus REST surface (login / list / pages / transcript+image
files); ``plan_collection_export`` resolves it into items; and
``bulk_stream_upload`` pushes their bytes through the shared bulk engine —
exercising batched presign, the ConflictPolicy guard (overwrite/skip/error),
and the tracker — into a genuine ThreadedMotoServer S3.

One stdlib ``http.server`` stands in for both the Transkribus REST/file server
and the HCP ``/auth/token`` + bulk-``/objects/presign`` + ``HEAD /objects/{key}``
endpoints; moto provides the real S3.
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

from rahcp_client import BulkStreamConfig, ConflictPolicy, HCPClient, bulk_stream_upload
from rahcp_tracker import SqliteTracker
from rahcp_transkribus import (
    TranskribusClient,
    fetch_item_bytes,
    plan_collection_export,
)

pytestmark = pytest.mark.asyncio

BUCKET = "transkribus-e2e"
REGION = "us-east-1"
COLLECTION = 7
DOC_ID = 100
DOC_SLUG = f"{DOC_ID}_DocA"

LOGIN_XML = "<trpUserLogin><sessionId>E2E-SESSION</sessionId></trpUserLogin>"
PAGE_XML_1 = b"<PcGts>transcript-one</PcGts>"
PAGE_XML_2 = b"<PcGts>transcript-two</PcGts>"


def _real_jpeg(color: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, "JPEG")
    return buf.getvalue()


IMG_1 = _real_jpeg("red")
IMG_2 = _real_jpeg("blue")

FILES = {
    "/files/ts/0001.xml": (PAGE_XML_1, "application/xml"),
    "/files/ts/0002.xml": (PAGE_XML_2, "application/xml"),
    "/files/img/0001.jpg": (IMG_1, "image/jpeg"),
    "/files/img/0002.jpg": (IMG_2, "image/jpeg"),
}

# Keys plan_collection_export produces for the fixture collection.
KEY_TS_1 = f"{COLLECTION}/{DOC_SLUG}/page/0001.xml"
KEY_TS_2 = f"{COLLECTION}/{DOC_SLUG}/page/0002.xml"
KEY_IMG_1 = f"{COLLECTION}/{DOC_SLUG}/images/0001.jpg"
KEY_IMG_2 = f"{COLLECTION}/{DOC_SLUG}/images/0002.jpg"
ALL_KEYS = {KEY_TS_1, KEY_TS_2, KEY_IMG_1, KEY_IMG_2}
EXPECTED_BYTES = {
    KEY_TS_1: PAGE_XML_1,
    KEY_TS_2: PAGE_XML_2,
    KEY_IMG_1: IMG_1,
    KEY_IMG_2: IMG_2,
}


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
def fake_server(s3_client):
    """Transkribus REST/file server + HCP auth/presign/HEAD, all backed by moto."""

    def _pages(host: str) -> list[dict]:
        return [
            {
                "pageNr": 1,
                "url": f"http://{host}/files/img/0001.jpg",
                "imgFileName": "0001.jpg",
                "tsList": {
                    "transcripts": [
                        {
                            "fileName": "0001.xml",
                            "url": f"http://{host}/files/ts/0001.xml",
                            "status": "GT",
                        }
                    ]
                },
            },
            {
                "pageNr": 2,
                "url": f"http://{host}/files/img/0002.jpg",
                "imgFileName": "0002.jpg",
                "tsList": {
                    "transcripts": [
                        {
                            "fileName": "0002.xml",
                            "url": f"http://{host}/files/ts/0002.xml",
                            "status": "GT",
                        }
                    ]
                },
            },
        ]

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
            path = urlparse(self.path).path
            if path in FILES:
                body, ctype = FILES[path]
                self._send(200, body, ctype)
                return
            if path.endswith(f"/collections/{COLLECTION}/list"):
                self._send(
                    200, json.dumps([{"docId": DOC_ID, "title": "DocA"}]).encode()
                )
                return
            if path.endswith(f"/collections/{COLLECTION}/{DOC_ID}/pages"):
                host = self.headers.get("Host", "127.0.0.1")
                self._send(200, json.dumps(_pages(host)).encode())
                return
            self._send(404, b"{}")  # pragma: no cover

        def do_HEAD(self):
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
            if path.endswith("/auth/login"):
                self._send(200, LOGIN_XML.encode(), "application/xml")
                return
            if path.endswith("/auth/logout"):
                self._send(200, b"")
                return
            if path.endswith("/auth/token"):
                self._send(
                    200,
                    json.dumps(
                        {"access_token": "test-token", "token_type": "bearer"}
                    ).encode(),
                )
                return
            body = json.loads(raw) if raw else {}
            if path.endswith("/objects/presign"):
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
                return
            self._send(404, b"{}")  # pragma: no cover

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


async def _stream(base_url, tracker, *, on_conflict=None, verify=False):
    """Plan the fixture collection and stream it to the bucket, like the CLI does."""
    async with (
        TranskribusClient("u", "p", base_url=f"{base_url}/TrpServer/rest") as tk,
        HCPClient(
            endpoint=f"{base_url}/api/v1", username="u", password="p", verify_ssl=False
        ) as hcp,
    ):
        items = await plan_collection_export(tk, COLLECTION, status="GT")
        items_by_id = {item.key: item for item in items}
        stream_items = [(item.key, item.key) for item in items]

        async def fetch(fetch_id: str) -> bytes:
            return await fetch_item_bytes(tk, items_by_id[fetch_id])

        return await bulk_stream_upload(
            BulkStreamConfig(
                client=hcp,
                bucket=BUCKET,
                tracker=tracker,
                workers=3,
                on_conflict=on_conflict,
                verify_upload=verify,
            ),
            stream_items,
            fetch,
        )


async def test_export_stream_lands_in_moto_and_counts_match(
    s3_client, fake_server, tmp_path
):
    tracker = SqliteTracker(tmp_path / "e2e.db")
    stats = await _stream(fake_server, tracker, verify=True)

    assert stats.ok == len(ALL_KEYS)
    assert stats.errors == 0
    for key, expected in EXPECTED_BYTES.items():
        assert s3_client.get_object(Bucket=BUCKET, Key=key)["Body"].read() == expected
    assert tracker.summary()["done"] == len(ALL_KEYS)
    tracker.close()


async def test_conflict_skip_leaves_existing_object_untouched(
    s3_client, fake_server, tmp_path
):
    s3_client.put_object(Bucket=BUCKET, Key=KEY_TS_1, Body=b"PRE-EXISTING")
    tracker = SqliteTracker(tmp_path / "e2e.db")

    stats = await _stream(fake_server, tracker, on_conflict=ConflictPolicy.skip)

    assert stats.skipped == 1
    assert stats.ok == len(ALL_KEYS) - 1
    # The pre-existing object was NOT overwritten.
    assert (
        s3_client.get_object(Bucket=BUCKET, Key=KEY_TS_1)["Body"].read()
        == b"PRE-EXISTING"
    )


async def test_conflict_error_records_conflict_for_existing_key(
    s3_client, fake_server, tmp_path
):
    s3_client.put_object(Bucket=BUCKET, Key=KEY_IMG_1, Body=b"PRE-EXISTING")
    tracker = SqliteTracker(tmp_path / "e2e.db")

    stats = await _stream(fake_server, tracker, on_conflict=ConflictPolicy.error)

    assert stats.errors == 1
    assert stats.ok == len(ALL_KEYS) - 1
    details = {key: reason for key, _size, reason in tracker.error_details()}
    assert KEY_IMG_1 in details
    assert (details[KEY_IMG_1] or "").startswith("conflict:")
    tracker.close()


async def test_conflict_overwrite_replaces_existing_object(
    s3_client, fake_server, tmp_path
):
    s3_client.put_object(Bucket=BUCKET, Key=KEY_TS_1, Body=b"PRE-EXISTING")
    tracker = SqliteTracker(tmp_path / "e2e.db")

    stats = await _stream(fake_server, tracker, on_conflict=ConflictPolicy.overwrite)

    assert stats.ok == len(ALL_KEYS)
    assert stats.skipped == 0
    # Overwritten with the real transcript bytes.
    assert (
        s3_client.get_object(Bucket=BUCKET, Key=KEY_TS_1)["Body"].read() == PAGE_XML_1
    )
    tracker.close()
