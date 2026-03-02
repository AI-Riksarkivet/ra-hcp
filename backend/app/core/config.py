"""Configuration for MAPI and S3 services."""

from __future__ import annotations

import base64
import hashlib
from typing import Literal

from pydantic_settings import BaseSettings

# App runs from backend/ so .env lives one level up.
_ENV_FILE = "../.env"


class MapiSettings(BaseSettings):
    """HCP Management API configuration (from environment / .env)."""

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}

    hcp_host: str = "admin.hcp.example.com"
    hcp_port: int = 9090
    hcp_username: str = ""
    hcp_password: str = ""
    hcp_auth_type: Literal["hcp", "ad"] = "hcp"
    hcp_verify_ssl: bool = False
    hcp_timeout: int = 60


class S3Settings(BaseSettings):
    """HCP S3 data-plane configuration.

    Reuses HCP_USERNAME / HCP_PASSWORD for credential derivation.
    Only S3-specific values (endpoint, region) use the S3_ prefix.
    """

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}

    # Reuse same env vars as MAPI
    hcp_username: str = ""
    hcp_password: str = ""
    hcp_verify_ssl: bool = False

    # S3-specific (S3_ prefix in env)
    s3_endpoint_url: str = "https://s3.hcp.example.com"
    s3_region: str = "us-east-1"

    @property
    def endpoint_url(self) -> str:
        return self.s3_endpoint_url

    @property
    def region(self) -> str:
        return self.s3_region

    @property
    def verify_ssl(self) -> bool:
        return self.hcp_verify_ssl

    @property
    def access_key(self) -> str:
        """Base64-encoded username (HCP S3 convention)."""
        return base64.b64encode(self.hcp_username.encode()).decode()

    @property
    def secret_key(self) -> str:
        """MD5-hashed password (HCP S3 convention)."""
        return hashlib.md5(self.hcp_password.encode()).hexdigest()


class CacheSettings(BaseSettings):
    """Redis cache configuration."""

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}

    redis_url: str = ""  # Empty = no caching
    cache_default_ttl: int = 300  # 5 min — MAPI tenant/namespace listings
    cache_stats_ttl: int = 60  # 1 min — statistics, chargeback
    cache_config_ttl: int = 600  # 10 min — consoleSecurity, permissions, etc.
    cache_s3_list_ttl: int = 120  # 2 min — bucket/object listings
    cache_s3_meta_ttl: int = 300  # 5 min — head_bucket, head_object, ACLs
    cache_key_prefix: str = "hcp"


class AuthSettings(BaseSettings):
    """API authentication settings."""

    model_config = {"env_file": _ENV_FILE, "extra": "ignore"}

    api_secret_key: str = "change-me-in-production"
    api_token_expire_minutes: int = 480  # 8 hours
