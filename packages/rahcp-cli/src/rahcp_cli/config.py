"""YAML config file with named profiles.

Config file: ~/.rahcp/config.yaml (or --config / RAHCP_CONFIG)

Example::

    default: dev

    profiles:
      dev:
        endpoint: http://localhost:8000/api/v1
        username: admin
        password: secret
        tenant: dev-ai
      prod:
        endpoint: http://localhost:8000/api/v1
        username: prod-user
        password: secret
        tenant: prod-archive
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_DIR = Path.home() / ".rahcp"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


class Profile(BaseModel):
    """A named connection profile."""

    endpoint: str = "http://localhost:8000/api/v1"
    username: str = ""
    password: str = ""
    tenant: str = ""
    verify_ssl: bool = True


class CLIConfig(BaseModel):
    """Config with named profiles."""

    default: str = ""
    profiles: dict[str, Profile] = {}

    def resolve(self, name: str | None = None) -> Profile:
        """Resolve a profile by name, falling back to default."""
        key = name or self.default
        if key and key in self.profiles:
            return self.profiles[key]
        if len(self.profiles) == 1:
            return next(iter(self.profiles.values()))
        return Profile()


def load_config(path: str | None = None) -> CLIConfig:
    """Load config from a YAML file.

    Resolution: explicit path > RAHCP_CONFIG env > ~/.rahcp/config.yaml
    """
    config_path = Path(path) if path else CONFIG_PATH
    if not config_path.exists():
        return CLIConfig()
    try:
        raw = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return CLIConfig()

    # Multi-profile format
    if "profiles" in raw:
        return CLIConfig(
            default=raw.get("default", ""),
            profiles={
                name: Profile(**vals)
                for name, vals in raw["profiles"].items()
                if isinstance(vals, dict)
            },
        )

    # Flat format (backwards compat) — single "default" profile
    return CLIConfig(
        default="default",
        profiles={
            "default": Profile(**{k: v for k, v in raw.items() if isinstance(v, str)})
        },
    )
