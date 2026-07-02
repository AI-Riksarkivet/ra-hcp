"""End-to-end integration test for Transkribus change detection against real moto S3.

Exercises the exact sequence the ``rahcp transkribus upload --check-updates`` CLI
runs — plan → ``refresh_stale_transcripts`` (drop changed keys from the tracker) →
``bulk_stream_upload`` (overwrite) → record versions — against a genuine
ThreadedMotoServer S3 and a *mutable* fake Transkribus server.

The scenario is the whole point of the feature: a transcript re-corrected in
Transkribus keeps the same object key but gets a new ``tsId``. We assert that a
second sync re-fetches ONLY that transcript, that its bytes in the bucket really
change to the corrected version, and that nothing else is touched.
"""

from __future__ import annotations

import asyncio
import io
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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
    TranscriptVersionStore,
    TranskribusClient,
    fetch_item_bytes,
    plan_collection_export,
    refresh_stale_transcripts,
    transcript_versions,
)

pytestmark = pytest.mark.asyncio

BUCKET = "tk-change"
REGION = "us-east-1"
COLLECTION = 7
DOC_ID = 100
SLUG = f"{DOC_ID}_DocA"
LOGIN_XML = "<trpUserLogin><sessionId>S</sessionId></trpUserLogin>"

# Object keys the exporter produces for this fixture.
KEY_TS1 = f"{COLLECTION}/{SLUG}/page/0001.xml"
KEY_TS2 = f"{COLLECTION}/{SLUG}/page/0002.xml"
KEY_IMG1 = f"{COLLECTION}/{SLUG}/images/0001.jpg"
KEY_IMG2 = f"{COLLECTION}/{SLUG}/images/0002.jpg"


def _jpeg(color: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, "JPEG")
    return buf.getvalue()


IMG1, IMG2 = _jpeg("red"), _jpeg("blue")
TS2_XML = b"<PcGts>page-two-unchanged</PcGts>"


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class _State:
    """Mutable Transkribus state so a test can 'correct' page 1's transcript."""

    def __init__(self) -> None:
        self.ts1_id = 1001
        self.ts1_xml = b"<PcGts>page-one-version-1</PcGts>"

    def correct_page1(self, *, new_id: int, new_xml: bytes) -> None:
        self.ts1_id = new_id
        self.ts1_xml = new_xml


@pytest.fixture
def moto_base():
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=_free_port())
    server.start()
    host, port = server.get_host_and_port()
    base = f"http://{host}:{port}"
    httpx.post(f"{base}/moto-api/reset")
    yield base
    server.stop()


@pytest.fixture
def s3(moto_base: str):
    client = boto3.client(
        "s3",
        endpoint_url=moto_base,
        aws_access_key_id="t",
        aws_secret_access_key="t",
        region_name=REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    client.create_bucket(Bucket=BUCKET)
    return client


@pytest.fixture
def state() -> _State:
    return _State()


@pytest.fixture
def server(s3, state: _State):
    """Mutable Transkribus REST/file server + HCP auth/presign/HEAD over moto."""

    def pages(host: str) -> list[dict]:
        return [
            {
                "pageNr": 1,
                "url": f"http://{host}/files/img/0001.jpg",
                "imgFileName": "0001.jpg",
                "tsList": {
                    "transcripts": [
                        {
                            "fileName": "0001.xml",
                            "status": "GT",
                            "tsId": state.ts1_id,
                            "url": f"http://{host}/files/ts/0001.xml",
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
                            "status": "GT",
                            "tsId": 2002,
                            "url": f"http://{host}/files/ts/0002.xml",
                        }
                    ]
                },
            },
        ]

    class H(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002 — base API name
            pass

        def _send(self, code, body=b"", ctype="application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            files = {
                "/files/ts/0001.xml": state.ts1_xml,
                "/files/ts/0002.xml": TS2_XML,
                "/files/img/0001.jpg": IMG1,
                "/files/img/0002.jpg": IMG2,
            }
            if path in files:
                self._send(200, files[path], "application/octet-stream")
                return
            if path.endswith(f"/collections/{COLLECTION}/list"):
                self._send(
                    200, json.dumps([{"docId": DOC_ID, "title": "DocA"}]).encode()
                )
                return
            if path.endswith(f"/collections/{COLLECTION}/{DOC_ID}/pages"):
                host = self.headers.get("Host", "127.0.0.1")
                self._send(200, json.dumps(pages(host)).encode())
                return
            self._send(404, b"{}")  # pragma: no cover

        def do_HEAD(self):
            path = urlparse(self.path).path
            bucket = path.split("/buckets/")[1].split("/objects/")[0]
            key = path.split("/objects/", 1)[1]
            try:
                meta = s3.head_object(Bucket=bucket, Key=key)
            except ClientError:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", str(meta["ContentLength"]))
            self.end_headers()

        def do_POST(self):
            path = urlparse(self.path).path
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b""
            if path.endswith("/auth/login"):
                self._send(200, LOGIN_XML.encode(), "application/xml")
                return
            if path.endswith("/auth/logout"):
                self._send(200, b"")
                return
            if path.endswith("/auth/token"):
                self._send(
                    200,
                    json.dumps({"access_token": "t", "token_type": "bearer"}).encode(),
                )
                return
            body = json.loads(raw) if raw else {}
            if path.endswith("/objects/presign"):
                bucket = path.split("/buckets/")[1].split("/objects")[0]
                urls = [
                    {
                        "key": k,
                        "url": s3.generate_presigned_url(
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

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


async def _sync(base: str, tracker_path: Path, version_db: Path):
    """Run the exact CLI `upload --check-updates` sequence once; return stats."""
    tracker = SqliteTracker(tracker_path)
    store = TranscriptVersionStore(version_db)
    async with (
        TranskribusClient("u", "p", base_url=f"{base}/TrpServer/rest") as tk,
        HCPClient(
            endpoint=f"{base}/api/v1", username="u", password="p", verify_ssl=False
        ) as hcp,
    ):
        items = await plan_collection_export(tk, COLLECTION, status="GT")
        await refresh_stale_transcripts(items, tracker, store, set())

        by_id = {it.key: it for it in items}
        stream_items = [(it.key, it.key) for it in items]

        async def fetch(fid: str) -> bytes:
            return await fetch_item_bytes(tk, by_id[fid])

        stats = await bulk_stream_upload(
            BulkStreamConfig(
                client=hcp,
                bucket=BUCKET,
                tracker=tracker,
                workers=3,
                on_conflict=ConflictPolicy.overwrite,
            ),
            stream_items,
            fetch,
        )
        done = await asyncio.to_thread(tracker.done_keys)
        store.set_many(transcript_versions(items, done))
    store.close()
    tracker.close()
    return stats


async def test_change_detection_reuploads_only_the_corrected_transcript(
    s3, server, state: _State, tmp_path: Path
):
    tracker_path = tmp_path / "tk.db"
    version_db = tmp_path / "tk.db.versions"

    # ── First sync: everything lands, versions recorded ──────────────
    first = await _sync(server, tracker_path, version_db)
    assert first.ok == 4  # 2 transcripts + 2 images
    assert (
        s3.get_object(Bucket=BUCKET, Key=KEY_TS1)["Body"].read()
        == b"<PcGts>page-one-version-1</PcGts>"
    )

    # ── No changes → a re-sync uploads nothing ───────────────────────
    unchanged = await _sync(server, tracker_path, version_db)
    assert unchanged.ok == 0
    assert unchanged.skipped == 0  # producer filters done keys before the workers

    # ── Correct page 1's transcript in Transkribus (new tsId + bytes) ─
    corrected = b"<PcGts>page-one-version-2-CORRECTED</PcGts>"
    state.correct_page1(new_id=1002, new_xml=corrected)

    third = await _sync(server, tracker_path, version_db)

    # Only the corrected transcript was re-fetched and re-uploaded.
    assert third.ok == 1
    # Its bytes in the bucket actually changed to the corrected version.
    assert s3.get_object(Bucket=BUCKET, Key=KEY_TS1)["Body"].read() == corrected
    # The unchanged transcript and both images were left exactly as they were.
    assert s3.get_object(Bucket=BUCKET, Key=KEY_TS2)["Body"].read() == TS2_XML
    assert s3.get_object(Bucket=BUCKET, Key=KEY_IMG1)["Body"].read() == IMG1

    # ── And a fourth sync (no further change) is a no-op again ────────
    fourth = await _sync(server, tracker_path, version_db)
    assert fourth.ok == 0


async def test_without_change_detection_correction_is_missed(
    s3, server, state: _State, tmp_path: Path
):
    """Control: same correction, but no version store → the old copy stays (the bug we fixed)."""
    tracker = SqliteTracker(tmp_path / "tk.db")

    async def plain_sync() -> None:
        async with (
            TranskribusClient("u", "p", base_url=f"{server}/TrpServer/rest") as tk,
            HCPClient(
                endpoint=f"{server}/api/v1",
                username="u",
                password="p",
                verify_ssl=False,
            ) as hcp,
        ):
            items = await plan_collection_export(tk, COLLECTION, status="GT")
            by_id = {it.key: it for it in items}
            stream = [(it.key, it.key) for it in items]

            async def fetch(fid: str) -> bytes:
                return await fetch_item_bytes(tk, by_id[fid])

            await bulk_stream_upload(
                BulkStreamConfig(
                    client=hcp,
                    bucket=BUCKET,
                    tracker=tracker,
                    workers=3,
                    on_conflict=ConflictPolicy.skip,
                ),
                stream,
                fetch,
            )

    await plain_sync()
    state.correct_page1(new_id=1002, new_xml=b"<PcGts>CORRECTED-but-missed</PcGts>")
    await plain_sync()

    # Without change detection the tracker skips the same key → old bytes remain.
    assert (
        s3.get_object(Bucket=BUCKET, Key=KEY_TS1)["Body"].read()
        == b"<PcGts>page-one-version-1</PcGts>"
    )
    tracker.close()
