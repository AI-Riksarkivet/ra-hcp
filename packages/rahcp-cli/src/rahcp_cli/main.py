"""Entry point for the rahcp CLI."""

from __future__ import annotations

import typer

from rahcp_cli import auth, namespace, s3
from rahcp_cli.config import load_config

app = typer.Typer(
    name="rahcp",
    help="CLI for HCP Unified API",
    no_args_is_help=True,
)

app.add_typer(auth.app, name="auth")
app.add_typer(s3.app, name="s3")
app.add_typer(namespace.app, name="ns")


@app.callback()
def main(
    ctx: typer.Context,
    config: str = typer.Option(
        None,
        "--config",
        envvar="RAHCP_CONFIG",
        help="Path to config YAML",
    ),
    profile: str = typer.Option(
        None,
        "--profile",
        "-c",
        envvar="HCP_PROFILE",
        help="Named profile from config",
    ),
    endpoint: str = typer.Option(
        None,
        "--endpoint",
        "-e",
        envvar="HCP_ENDPOINT",
        help="HCP API base URL (overrides profile)",
    ),
    username: str = typer.Option(
        None,
        "--username",
        "-u",
        envvar="HCP_USERNAME",
        help="Username (overrides profile)",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        envvar="HCP_PASSWORD",
        help="Password (overrides profile)",
    ),
    tenant_name: str = typer.Option(
        None,
        "--tenant",
        "-t",
        envvar="HCP_TENANT",
        help="HCP tenant (overrides profile)",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output raw JSON",
    ),
) -> None:
    """CLI flags > env vars > profile > defaults."""
    ctx.ensure_object(dict)

    cfg = load_config(config)
    p = cfg.resolve(profile)

    # CLI flags > env vars > profile > defaults
    ctx.obj["endpoint"] = endpoint or p.endpoint
    ctx.obj["username"] = username or p.username
    ctx.obj["password"] = password or p.password
    ctx.obj["tenant"] = tenant_name or p.tenant
    ctx.obj["json"] = output_json
