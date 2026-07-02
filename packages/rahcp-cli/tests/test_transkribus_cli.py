"""Tests for the `rahcp transkribus` CLI subcommands."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import respx
from typer.testing import CliRunner

from rahcp_cli.main import app

runner = CliRunner()

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
    }
]


def _mock_transkribus(router: respx.Router) -> None:
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
    router.get("https://files.example/ts1.xml").mock(
        return_value=httpx.Response(200, content=b"<PcGts>xml</PcGts>")
    )
    router.get("https://files.example/img1.jpg").mock(
        return_value=httpx.Response(200, content=b"\xff\xd8jpeg")
    )


class _FakeHCPClient:
    """Fake HCPClient whose S3 ops skip HTTP (per-key upload fallback path)."""

    def __init__(self):
        from rahcp_client.bulk.protocol import TransferSettings

        self.s3 = MagicMock()
        self.s3.presign_bulk = AsyncMock(return_value={})
        self.s3.upload = AsyncMock(return_value='"etag"')
        self.s3.head = AsyncMock(side_effect=Exception("not found"))
        self.transfer_settings = TransferSettings(
            verify_ssl=False, timeout=30.0, multipart_threshold=100 * 1024 * 1024
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


# ── Validation guards (no network) ──────────────────────────────────


def test_export_requires_credentials(tmp_path):
    result = runner.invoke(
        app,
        ["transkribus", "export", "42", "--tracker-db", str(tmp_path / "t.db")],
    )
    assert result.exit_code == 1
    assert "credentials required" in result.output


def test_export_rejects_invalid_format(tmp_path):
    result = runner.invoke(
        app,
        [
            "transkribus",
            "export",
            "42",
            "--format",
            "bogus",
            "--tracker-db",
            str(tmp_path / "t.db"),
        ],
    )
    assert result.exit_code == 1
    assert "Invalid --format" in result.output


def test_upload_rejects_invalid_on_conflict(tmp_path):
    result = runner.invoke(
        app,
        [
            "transkribus",
            "upload",
            "42",
            "mybucket",
            "--on-conflict",
            "bogus",
            "-U",
            "user",
            "-P",
            "pw",
            "--tracker-db",
            str(tmp_path / "t.db"),
        ],
    )
    assert result.exit_code == 1
    assert "Invalid --on-conflict" in result.output


# ── Happy paths (respx-mocked Transkribus) ──────────────────────────


@respx.mock
def test_export_local_writes_files(tmp_path):
    _mock_transkribus(respx.mock)
    out = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "transkribus",
            "export",
            "42",
            "-o",
            str(out),
            "-U",
            "user",
            "-P",
            "pw",
            "--tracker-db",
            str(tmp_path / "t.db"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Exported 2 files" in result.output
    assert (out / "42/100_Charter A/page/0001.xml").exists()
    assert (out / "42/100_Charter A/images/0001.jpg").exists()


@respx.mock
def test_upload_streams_to_bucket(tmp_path):
    _mock_transkribus(respx.mock)
    client = _FakeHCPClient()
    with patch("rahcp_cli.transkribus.make_client", return_value=client):
        result = runner.invoke(
            app,
            [
                "transkribus",
                "upload",
                "42",
                "mybucket",
                "--prefix",
                "medieval/",
                "--on-conflict",
                "overwrite",
                "-U",
                "user",
                "-P",
                "pw",
                "--tracker-db",
                str(tmp_path / "t.db"),
            ],
        )
    assert result.exit_code == 0, result.output
    assert "Uploaded 2 files" in result.output
    # Both items uploaded through the per-key fallback path with the prefix applied.
    assert client.s3.upload.call_count == 2
    uploaded_keys = {call.args[1] for call in client.s3.upload.call_args_list}
    assert uploaded_keys == {
        "medieval/42/100_Charter A/page/0001.xml",
        "medieval/42/100_Charter A/images/0001.jpg",
    }


@respx.mock
def test_upload_archive_dir_tees_local_copy(tmp_path):
    """--archive-dir keeps a local copy of every file while streaming to the bucket."""
    _mock_transkribus(respx.mock)
    archive = tmp_path / "archive"
    client = _FakeHCPClient()
    with patch("rahcp_cli.transkribus.make_client", return_value=client):
        result = runner.invoke(
            app,
            [
                "transkribus",
                "upload",
                "42",
                "mybucket",
                "--on-conflict",
                "overwrite",
                "--archive-dir",
                str(archive),
                "-U",
                "user",
                "-P",
                "pw",
                "--tracker-db",
                str(tmp_path / "t.db"),
            ],
        )
    assert result.exit_code == 0, result.output
    # Uploaded to the bucket AND written to the local archive (both copies).
    assert client.s3.upload.call_count == 2
    assert (
        archive / "42/100_Charter A/page/0001.xml"
    ).read_bytes() == b"<PcGts>xml</PcGts>"
    assert (archive / "42/100_Charter A/images/0001.jpg").exists()


@respx.mock
def test_upload_fail_on_error_exits_nonzero(tmp_path):
    """With errors and --fail-on-error (default), the command exits non-zero for cron."""
    _mock_transkribus(respx.mock)
    client = _FakeHCPClient()
    # Key already exists → on-conflict=error records a conflict for every item.
    client.s3.head = AsyncMock(return_value={"content-length": "5"})
    with patch("rahcp_cli.transkribus.make_client", return_value=client):
        result = runner.invoke(
            app,
            [
                "transkribus",
                "upload",
                "42",
                "mybucket",
                "--on-conflict",
                "error",
                "-U",
                "user",
                "-P",
                "pw",
                "--tracker-db",
                str(tmp_path / "t.db"),
            ],
        )
    assert result.exit_code == 1
    assert "errors" in result.output


@respx.mock
def test_upload_no_fail_on_error_exits_zero(tmp_path):
    """--no-fail-on-error keeps exit 0 even when items failed."""
    _mock_transkribus(respx.mock)
    client = _FakeHCPClient()
    client.s3.head = AsyncMock(return_value={"content-length": "5"})
    with patch("rahcp_cli.transkribus.make_client", return_value=client):
        result = runner.invoke(
            app,
            [
                "transkribus",
                "upload",
                "42",
                "mybucket",
                "--on-conflict",
                "error",
                "--no-fail-on-error",
                "-U",
                "user",
                "-P",
                "pw",
                "--tracker-db",
                str(tmp_path / "t.db"),
            ],
        )
    assert result.exit_code == 0, result.output
