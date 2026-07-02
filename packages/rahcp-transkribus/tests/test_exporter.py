"""Unit tests for export planning and local collection export."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from rahcp_transkribus import (
    ExportFormat,
    ItemKind,
    TranskribusClient,
    export_collection,
    plan_collection_export,
)
from rahcp_transkribus.exporter import (
    _transcript_name,
    fetch_item_bytes,
    sanitize_filename,
)
from rahcp_transkribus.models import ExportItem
from rahcp_tracker import TransferStatus, TransferTracker

BASE = "https://transkribus.eu/TrpServer/rest"
LOGIN_XML = "<trpUserLogin><sessionId>S</sessionId></trpUserLogin>"

DOCS = [{"docId": 100, "title": "Charter A"}]
PAGES = [
    {
        "pageNr": 1,
        "url": "https://files.example/img1.jpg",
        "imgFileName": "0001.jpg",
        "tsList": {
            "transcripts": [
                {
                    "fileName": "0001.xml",
                    "url": "https://files.example/ts1.xml",
                    "status": "GT",
                }
            ]
        },
    },
    {
        "pageNr": 2,
        "url": "https://files.example/img2.jpg",
        "imgFileName": "0002.jpg",
        "tsList": {"transcripts": []},  # no GT transcript → whole page skipped
    },
]


def _mock_collection(router: respx.Router) -> None:
    router.post(f"{BASE}/auth/login").mock(
        return_value=httpx.Response(200, text=LOGIN_XML)
    )
    router.post(f"{BASE}/auth/logout").mock(return_value=httpx.Response(200))
    router.get(f"{BASE}/collections/42/list").mock(
        return_value=httpx.Response(200, json=DOCS)
    )
    router.get(f"{BASE}/collections/42/100/pages").mock(
        return_value=httpx.Response(200, json=PAGES)
    )


def _mock_files(router: respx.Router) -> None:
    router.get("https://files.example/ts1.xml").mock(
        return_value=httpx.Response(200, content=b"<PcGts>page-xml</PcGts>")
    )
    router.get("https://files.example/img1.jpg").mock(
        return_value=httpx.Response(200, content=b"\xff\xd8jpeg")
    )


# ── Naming ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "file_name,fmt,expected",
    [
        ("0001.xml", ExportFormat.page, "0001.xml"),
        ("0001.xml", ExportFormat.alto, "0001.alto.xml"),
        ("16020_16020.jpg.xml", ExportFormat.alto, "16020_16020.jpg.alto.xml"),
        (None, ExportFormat.page, "page_0005.xml"),
    ],
)
def test_transcript_name(file_name, fmt, expected):
    assert _transcript_name(file_name, 5, fmt) == expected


def test_sanitize_filename_replaces_unsafe_chars():
    assert sanitize_filename("A/B:C") == "A_B_C"


def test_sanitize_filename_empty_falls_back():
    assert sanitize_filename("   ") == "untitled"
    assert sanitize_filename("") == "untitled"


# ── Planning ────────────────────────────────────────────────────────


@respx.mock
async def test_plan_collection_export_builds_transcript_and_image_items():
    _mock_collection(respx.mock)
    async with TranskribusClient("u", "p") as client:
        items = await plan_collection_export(client, 42, status="GT")

    # page 1 → transcript + image; page 2 has no transcript → skipped entirely
    assert len(items) == 2
    kinds = {i.kind for i in items}
    assert kinds == {ItemKind.transcript, ItemKind.image}
    transcript = next(i for i in items if i.kind is ItemKind.transcript)
    image = next(i for i in items if i.kind is ItemKind.image)
    assert transcript.key == "42/100_Charter A/page/0001.xml"
    assert transcript.url == "https://files.example/ts1.xml"
    assert not transcript.convert_alto
    assert image.key == "42/100_Charter A/images/0001.jpg"


@respx.mock
async def test_plan_alto_marks_conversion_and_extension():
    _mock_collection(respx.mock)
    async with TranskribusClient("u", "p") as client:
        items = await plan_collection_export(client, 42, fmt=ExportFormat.alto)

    transcript = next(i for i in items if i.kind is ItemKind.transcript)
    assert transcript.key == "42/100_Charter A/alto/0001.alto.xml"
    assert transcript.convert_alto is True


@respx.mock
async def test_plan_without_images():
    _mock_collection(respx.mock)
    async with TranskribusClient("u", "p") as client:
        items = await plan_collection_export(client, 42, include_images=False)

    assert all(i.kind is ItemKind.transcript for i in items)
    assert len(items) == 1


@respx.mock
async def test_plan_uses_text_endpoint_when_transcript_url_missing():
    respx.mock.post(f"{BASE}/auth/login").mock(
        return_value=httpx.Response(200, text=LOGIN_XML)
    )
    respx.mock.post(f"{BASE}/auth/logout").mock(return_value=httpx.Response(200))
    respx.mock.get(f"{BASE}/collections/42/list").mock(
        return_value=httpx.Response(200, json=DOCS)
    )
    respx.mock.get(f"{BASE}/collections/42/100/pages").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "pageNr": 1,
                    "tsList": {"transcripts": [{"fileName": "0001.xml"}]},
                }
            ],
        )
    )
    async with TranskribusClient("u", "p") as client:
        items = await plan_collection_export(client, 42)

    assert items[0].url == f"{BASE}/collections/42/100/1/text"


# ── fetch_item_bytes ────────────────────────────────────────────────


@respx.mock
async def test_fetch_item_bytes_plain():
    _mock_collection(respx.mock)
    _mock_files(respx.mock)
    item = ExportItem(
        key="k",
        url="https://files.example/img1.jpg",
        kind=ItemKind.image,
        doc_id=100,
        page_nr=1,
    )
    async with TranskribusClient("u", "p") as client:
        data = await fetch_item_bytes(client, item)
    assert data == b"\xff\xd8jpeg"


@respx.mock
async def test_fetch_item_bytes_converts_alto(monkeypatch):
    _mock_collection(respx.mock)
    _mock_files(respx.mock)
    monkeypatch.setattr(
        "rahcp_transkribus.exporter.page_bytes_to_alto",
        lambda data: b"<alto>from:" + data + b"</alto>",
    )
    item = ExportItem(
        key="k",
        url="https://files.example/ts1.xml",
        kind=ItemKind.transcript,
        doc_id=100,
        page_nr=1,
        convert_alto=True,
    )
    async with TranskribusClient("u", "p") as client:
        data = await fetch_item_bytes(client, item)
    assert data == b"<alto>from:<PcGts>page-xml</PcGts></alto>"


# ── Local export ────────────────────────────────────────────────────


@respx.mock
async def test_export_collection_writes_files_and_marks_tracker(tmp_path: Path):
    _mock_collection(respx.mock)
    _mock_files(respx.mock)
    out = tmp_path / "out"
    tracker = TransferTracker(tmp_path / "t.db")

    async with TranskribusClient("u", "p") as client:
        stats = await export_collection(client, 42, out, tracker, workers=2)

    assert stats.ok == 2
    assert stats.errors == 0
    assert (
        out / "42/100_Charter A/page/0001.xml"
    ).read_bytes() == b"<PcGts>page-xml</PcGts>"
    assert (out / "42/100_Charter A/images/0001.jpg").exists()
    assert "42/100_Charter A/page/0001.xml" in tracker.done_keys()
    tracker.close()


@respx.mock
async def test_export_collection_resumes_from_tracker(tmp_path: Path):
    _mock_collection(respx.mock)
    _mock_files(respx.mock)
    out = tmp_path / "out"
    tracker = TransferTracker(tmp_path / "t.db")
    tracker.mark("42/100_Charter A/page/0001.xml", 10, TransferStatus.done)
    tracker.mark("42/100_Charter A/images/0001.jpg", 10, TransferStatus.done)
    tracker.flush()

    async with TranskribusClient("u", "p") as client:
        stats = await export_collection(client, 42, out, tracker, workers=2)

    assert stats.skipped == 2
    assert stats.ok == 0
    tracker.close()


@respx.mock
async def test_export_collection_prefix_applied(tmp_path: Path):
    _mock_collection(respx.mock)
    _mock_files(respx.mock)
    out = tmp_path / "out"
    tracker = TransferTracker(tmp_path / "t.db")

    async with TranskribusClient("u", "p") as client:
        await export_collection(
            client, 42, out, tracker, prefix="andraarkiv/", workers=1
        )

    assert (out / "andraarkiv/42/100_Charter A/page/0001.xml").exists()
    assert "andraarkiv/42/100_Charter A/page/0001.xml" in tracker.done_keys()
    tracker.close()


@respx.mock
async def test_export_collection_records_fetch_errors(tmp_path: Path):
    _mock_collection(respx.mock)
    # transcript fetch fails (404 = terminal), image succeeds
    respx.mock.get("https://files.example/ts1.xml").mock(
        return_value=httpx.Response(404)
    )
    respx.mock.get("https://files.example/img1.jpg").mock(
        return_value=httpx.Response(200, content=b"\xff\xd8jpeg")
    )
    out = tmp_path / "out"
    tracker = TransferTracker(tmp_path / "t.db")
    errors_seen: list[str] = []

    async with TranskribusClient("u", "p", retry_base_delay=0.0) as client:
        stats = await export_collection(
            client,
            42,
            out,
            tracker,
            workers=1,
            on_error=lambda key, exc: errors_seen.append(key),
        )

    assert stats.errors == 1
    assert stats.ok == 1
    assert errors_seen == ["42/100_Charter A/page/0001.xml"]
    details = tracker.error_details()
    assert (details[0][2] or "").startswith("download:")
    tracker.close()
