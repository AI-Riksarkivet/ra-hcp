"""Optional PAGE-XML → ALTO-XML conversion via the ``page-to-alto`` CLI.

Requires the ``alto`` extra (``pip install "rahcp-transkribus[alto]"``), which
pulls in ``ocrd-page-to-alto`` and its ``page-to-alto`` console script. The
conversion shells out to that binary — a one-way PAGE→ALTO transform.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from rahcp_transkribus.errors import TranskribusError

log = logging.getLogger(__name__)

_ALTO_BINARY = "page-to-alto"


def alto_available() -> bool:
    """Return whether the ``page-to-alto`` binary is on ``PATH``."""
    return shutil.which(_ALTO_BINARY) is not None


def page_bytes_to_alto(page_xml: bytes, *, alto_version: str = "4.2") -> bytes:
    """Convert PAGE-XML bytes to ALTO-XML bytes.

    Args:
        page_xml: PAGE-XML document bytes.
        alto_version: Target ALTO schema version.

    Returns:
        ALTO-XML document bytes.

    Raises:
        TranskribusError: If ``page-to-alto`` is not installed or the
            conversion fails.
    """
    if not alto_available():
        raise TranskribusError(
            "page-to-alto not found — install the ALTO extra: "
            'pip install "rahcp-transkribus[alto]"'
        )

    with tempfile.TemporaryDirectory(prefix="rahcp-alto-") as tmp:
        page_path = Path(tmp) / "page.xml"
        page_path.write_bytes(page_xml)
        try:
            result = subprocess.run(  # noqa: S603 — fixed binary, no shell
                [
                    _ALTO_BINARY,
                    "--alto-version",
                    alto_version,
                    "--no-check-words",
                    "--no-check-border",
                    "--dummy-word",
                    str(page_path),
                ],
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise TranskribusError(f"page-to-alto failed to run: {exc}") from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace").strip()
        raise TranskribusError(f"page-to-alto conversion failed: {stderr}")
    return result.stdout
