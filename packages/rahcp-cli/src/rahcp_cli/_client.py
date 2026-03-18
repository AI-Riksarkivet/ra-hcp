"""Shared client factory — auto-authenticates from config/flags/env."""

from __future__ import annotations

import typer


def make_client(ctx: typer.Context):  # type: ignore[no-untyped-def]  # noqa: ANN201
    """Create an HCPClient from resolved settings.

    Priority: CLI flags > env vars > config file > defaults.

    If username/password are available, the client auto-logs in on __aenter__.
    Tenant is passed during login so the backend routes to the correct HCP tenant.
    """
    from rahcp_client import HCPClient

    return HCPClient(
        endpoint=ctx.obj["endpoint"],
        username=ctx.obj.get("username", ""),
        password=ctx.obj.get("password", ""),
        tenant=ctx.obj.get("tenant"),
    )
