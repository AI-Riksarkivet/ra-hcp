"""Unit tests for the optional PAGE→ALTO conversion helper."""

from __future__ import annotations

import pytest

from rahcp_transkribus.alto import alto_available, page_bytes_to_alto
from rahcp_transkribus.errors import TranskribusError


def test_page_bytes_to_alto_raises_when_binary_missing(monkeypatch):
    monkeypatch.setattr("rahcp_transkribus.alto.shutil.which", lambda _: None)
    assert alto_available() is False
    with pytest.raises(TranskribusError, match="page-to-alto not found"):
        page_bytes_to_alto(b"<PcGts/>")


def test_page_bytes_to_alto_surfaces_conversion_failure(monkeypatch):
    monkeypatch.setattr(
        "rahcp_transkribus.alto.shutil.which", lambda _: "/usr/bin/page-to-alto"
    )

    class _Result:
        returncode = 1
        stdout = b""
        stderr = b"boom: bad page xml"

    monkeypatch.setattr(
        "rahcp_transkribus.alto.subprocess.run", lambda *a, **k: _Result()
    )
    with pytest.raises(TranskribusError, match="boom: bad page xml"):
        page_bytes_to_alto(b"<PcGts/>")


def test_page_bytes_to_alto_returns_stdout(monkeypatch):
    monkeypatch.setattr(
        "rahcp_transkribus.alto.shutil.which", lambda _: "/usr/bin/page-to-alto"
    )

    class _Result:
        returncode = 0
        stdout = b"<alto>ok</alto>"
        stderr = b""

    monkeypatch.setattr(
        "rahcp_transkribus.alto.subprocess.run", lambda *a, **k: _Result()
    )
    assert page_bytes_to_alto(b"<PcGts/>") == b"<alto>ok</alto>"
