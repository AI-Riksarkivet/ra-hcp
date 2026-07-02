"""Transkribus settings — configurable via environment variables."""

from __future__ import annotations

import os

TRANSKRIBUS_URL = os.environ.get(
    "TRANSKRIBUS_URL", "https://transkribus.eu/TrpServer/rest"
)
TRANSKRIBUS_TIMEOUT = float(os.environ.get("TRANSKRIBUS_TIMEOUT", "60"))


def resolve_verify_ssl(verify_ssl: bool | None = None) -> bool:
    """Resolve TLS verification, honouring the ``SKIP_SSL_VERIFY`` env var.

    An explicit ``verify_ssl`` argument wins. Otherwise verification is on
    unless ``SKIP_SSL_VERIFY`` is a truthy string (``1``/``true``/``yes``) —
    the escape hatch for TLS-intercepting corporate proxies.
    """
    if verify_ssl is not None:
        return verify_ssl
    return os.environ.get("SKIP_SSL_VERIFY", "").lower() not in ("1", "true", "yes")
