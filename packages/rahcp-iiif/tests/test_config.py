"""Tests for IIIF env-var configuration wiring."""

import importlib
import inspect

import rahcp_iiif.config as config
from rahcp_iiif.downloader import download_batch
from rahcp_iiif.manifest import build_image_url, file_extension, get_image_ids


def test_download_batch_defaults_come_from_config():
    defaults = {
        name: p.default
        for name, p in inspect.signature(download_batch).parameters.items()
    }
    assert defaults["base_url"] == config.IIIF_URL
    assert defaults["query_params"] == config.IIIF_QUERY_PARAMS
    assert defaults["timeout"] == config.IIIF_TIMEOUT


def test_manifest_helpers_default_to_config():
    sig_ids = inspect.signature(get_image_ids).parameters
    assert sig_ids["base_url"].default == config.IIIF_URL
    assert sig_ids["timeout"].default == config.IIIF_TIMEOUT

    assert (
        inspect.signature(build_image_url).parameters["query_params"].default
        == config.IIIF_QUERY_PARAMS
    )
    assert (
        inspect.signature(file_extension).parameters["query_params"].default
        == config.IIIF_QUERY_PARAMS
    )


def test_env_vars_override_config_at_import(monkeypatch):
    monkeypatch.setenv("IIIF_URL", "https://other-iiif.example.com")
    monkeypatch.setenv("IIIF_TIMEOUT", "12.5")
    monkeypatch.setenv("IIIF_QUERY_PARAMS", "full/,800/0/default.png")
    try:
        importlib.reload(config)
        assert config.IIIF_URL == "https://other-iiif.example.com"
        assert config.IIIF_TIMEOUT == 12.5
        assert config.IIIF_QUERY_PARAMS == "full/,800/0/default.png"
    finally:
        monkeypatch.undo()
        importlib.reload(config)
