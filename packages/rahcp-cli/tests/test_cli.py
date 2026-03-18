"""Tests for CLI commands — verify arg parsing and output formatting."""

import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from rahcp_cli.main import app

runner = CliRunner()


class FakeClient:
    """Fake HCPClient that skips HTTP entirely."""

    def __init__(self, **method_returns):
        self._token = "test-token"
        self.s3 = MagicMock()
        self.mapi = MagicMock()
        for attr, value in method_returns.items():
            parts = attr.split(".")
            obj = self
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], AsyncMock(return_value=value))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def request(self, *args, **kwargs):
        raise NotImplementedError("Use specific method mocks")


def _invoke(args, **method_returns):
    client = FakeClient(**method_returns)
    with (
        patch("rahcp_cli.s3.make_client", return_value=client),
        patch("rahcp_cli.namespace.make_client", return_value=client),
        patch("rahcp_cli.auth.make_client", return_value=client),
    ):
        result = runner.invoke(app, args)
    return result, client


# ── s3 ls (buckets) ────────────────────────────────────────────────


def test_s3_ls_buckets():
    result, _ = _invoke(
        ["s3", "ls"],
        **{"s3.list_buckets": {"buckets": [{"Name": "b1"}, {"Name": "b2"}]}},
    )
    assert result.exit_code == 0
    assert "b1" in result.output
    assert "b2" in result.output


def test_s3_ls_buckets_json():
    result, _ = _invoke(
        ["--json", "s3", "ls"],
        **{"s3.list_buckets": {"buckets": [{"Name": "b1"}]}},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["buckets"][0]["Name"] == "b1"


# ── s3 ls BUCKET (objects) ─────────────────────────────────────────


def test_s3_ls_objects():
    result, _ = _invoke(
        ["s3", "ls", "mybucket"],
        **{"s3.list_objects": {"objects": [{"Key": "file.txt", "Size": 100}]}},
    )
    assert result.exit_code == 0
    assert "file.txt" in result.output


def test_s3_ls_objects_with_prefix():
    result, client = _invoke(
        ["s3", "ls", "mybucket", "--prefix", "data/"],
        **{"s3.list_objects": {"objects": []}},
    )
    assert result.exit_code == 0
    client.s3.list_objects.assert_called_once_with(
        "mybucket", "data/", max_keys=100, continuation_token=None, delimiter=None
    )


# ── s3 presign ──────────────────────────────────────────────────────


def test_s3_presign():
    result, _ = _invoke(
        ["s3", "presign", "b", "k"],
        **{"s3.presign_get": "https://signed-url"},
    )
    assert result.exit_code == 0
    assert "https://signed-url" in result.output


# ── ns list ─────────────────────────────────────────────────────────


def test_ns_list():
    result, _ = _invoke(
        ["ns", "list", "my-tenant"],
        **{"mapi.list_namespaces": {"name": ["ns1", "ns2"]}},
    )
    assert result.exit_code == 0
    assert "ns1" in result.output
    assert "ns2" in result.output


# ── ns get ──────────────────────────────────────────────────────────


def test_ns_get_json():
    result, _ = _invoke(
        ["--json", "ns", "get", "t", "ns1"],
        **{"mapi.get_namespace": {"name": "ns1", "hardQuota": "10 GB"}},
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "ns1"


# ── ns export ───────────────────────────────────────────────────────


def test_ns_export():
    result, _ = _invoke(
        ["ns", "export", "t", "ns1"],
        **{
            "mapi.export_namespace": {"version": "1.0", "namespaces": [{"name": "ns1"}]}
        },
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["version"] == "1.0"


# ── auth whoami ─────────────────────────────────────────────────────


def test_auth_whoami():
    payload = (
        base64.urlsafe_b64encode(
            json.dumps({"sub": "testuser", "tenant": "t1"}).encode()
        )
        .decode()
        .rstrip("=")
    )
    client = FakeClient()
    client._token = f"header.{payload}.signature"
    with patch("rahcp_cli.auth.make_client", return_value=client):
        result = runner.invoke(app, ["auth", "whoami"])
    assert result.exit_code == 0
    assert "testuser" in result.output
    assert "t1" in result.output
