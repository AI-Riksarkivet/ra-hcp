"""Tests for the storage factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pydantic import SecretStr

from app.core.config import S3Settings, StorageSettings
from app.services.storage.adapters.generic_boto3 import GenericBoto3Storage
from app.services.storage.adapters.hcp import HcpStorage
from app.services.storage.factory import create_cached_storage, create_storage


@pytest.fixture
def hcp_storage_settings() -> StorageSettings:
    return StorageSettings(storage_backend="hcp")


@pytest.fixture
def minio_storage_settings() -> StorageSettings:
    return StorageSettings(
        storage_backend="minio",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key="admin",
        s3_secret_key=SecretStr("secret"),
        s3_addressing_style="path",
    )


@pytest.fixture
def generic_storage_settings() -> StorageSettings:
    return StorageSettings(
        storage_backend="generic",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key="admin",
        s3_secret_key=SecretStr("secret"),
    )


@pytest.fixture
def s3_settings() -> S3Settings:
    return S3Settings(
        hcp_username="testuser",
        hcp_password="testpass",
        hcp_verify_ssl=False,
        s3_endpoint_url="https://s3.test.com",
        s3_region="us-east-1",
    )


# -- Plain storage creation ------------------------------------------------


def test_create_storage_hcp(
    hcp_storage_settings: StorageSettings, s3_settings: S3Settings
):
    with patch("app.services.storage.adapters.hcp.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        storage = create_storage(
            hcp_storage_settings,
            "access",
            "secret",
            s3_settings=s3_settings,
        )
    assert isinstance(storage, HcpStorage)


def test_create_storage_minio(minio_storage_settings: StorageSettings):
    with patch("app.services.storage.adapters.generic_boto3.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        storage = create_storage(minio_storage_settings, "access", "secret")
    assert isinstance(storage, GenericBoto3Storage)


def test_create_storage_generic(generic_storage_settings: StorageSettings):
    with patch("app.services.storage.adapters.generic_boto3.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        storage = create_storage(generic_storage_settings, "access", "secret")
    assert isinstance(storage, GenericBoto3Storage)


def test_create_storage_unknown_backend():
    settings = StorageSettings(storage_backend="hcp")
    # Bypass Pydantic validation to test the match/case default branch
    object.__setattr__(settings, "storage_backend", "unknown")
    with pytest.raises(ValueError, match="Unknown storage backend"):
        create_storage(settings, "access", "secret")


def test_create_storage_hcp_requires_s3_settings(
    hcp_storage_settings: StorageSettings,
):
    with pytest.raises(ValueError, match="s3_settings required"):
        create_storage(hcp_storage_settings, "access", "secret")


# -- Cached storage creation -----------------------------------------------


def test_create_cached_storage_hcp(
    hcp_storage_settings: StorageSettings, s3_settings: S3Settings
):
    from app.core.config import CacheSettings
    from app.services.cached_storage import CachedStorage

    with patch("app.services.storage.adapters.hcp.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        storage = create_cached_storage(
            hcp_storage_settings,
            "access",
            "secret",
            cache=MagicMock(),
            cache_settings=CacheSettings(),
            s3_settings=s3_settings,
        )
    assert isinstance(storage, CachedStorage)


def test_create_cached_storage_minio(minio_storage_settings: StorageSettings):
    from app.core.config import CacheSettings
    from app.services.cached_storage import CachedStorage

    with patch("app.services.storage.adapters.generic_boto3.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        storage = create_cached_storage(
            minio_storage_settings,
            "access",
            "secret",
            cache=MagicMock(),
            cache_settings=CacheSettings(),
        )
    assert isinstance(storage, CachedStorage)
