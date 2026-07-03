"""Test bootstrap for the rahcp workspace.

The sibling SDK modules (``rahcp_client``, ``rahcp_tracker``, ``rahcp_iiif``,
``rahcp_transkribus``, ``rahcp_validate``, ``rahcp_etl``) live in
``packages/*/src`` as separate uv workspace members. They are bundled into the
single ``rahcp`` wheel at build time, but uv does not install workspace members
as editable in the dev venv, so their ``src`` roots are added to ``sys.path``
here to make them importable for the test suite. The published package is
unaffected — it ships the bundled copies.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGES = Path(__file__).parent / "packages"

for _src in sorted(_PACKAGES.glob("rahcp-*/src")):
    _path = str(_src)
    if _path not in sys.path:
        sys.path.insert(0, _path)
