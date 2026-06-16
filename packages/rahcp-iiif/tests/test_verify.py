"""Tests for batch completeness verification."""

import httpx
import pytest
import respx

from rahcp_iiif.verify import BatchState, verify_batches

BASE = "https://test-iiif.example.com"


def _manifest(batch: str, n: int) -> dict:
    """A manifest whose canvas ids embed the image id, like Riksarkivet's."""
    return {
        "items": [
            {"id": f"https://x/arkis!{batch}_{i:05d}/canvas"} for i in range(1, n + 1)
        ]
    }


def _done(batch: str, n: int) -> set[str]:
    """Tracker done-keys as the downloader writes them: ``<batch>/<image>.jpg``."""
    return {f"{batch}/{batch}_{i:05d}.jpg" for i in range(1, n + 1)}


@pytest.mark.asyncio
@respx.mock
async def test_complete_batch_has_no_deficiency():
    respx.get(f"{BASE}/arkis!A1/manifest").mock(
        return_value=httpx.Response(200, json=_manifest("A1", 3))
    )
    report = await verify_batches(["A1"], _done("A1", 3), base_url=BASE, workers=4)

    assert len(report.complete) == 1
    assert report.deficient == []
    assert report.total_missing_images == 0


@pytest.mark.asyncio
@respx.mock
async def test_short_batch_is_detected_with_missing_count():
    respx.get(f"{BASE}/arkis!A0076522/manifest").mock(
        return_value=httpx.Response(200, json=_manifest("A0076522", 394))
    )
    report = await verify_batches(
        ["A0076522"], _done("A0076522", 2), base_url=BASE, workers=4
    )

    assert len(report.short) == 1
    result = report.short[0]
    assert result.state is BatchState.short
    assert result.expected == 394
    assert result.got == 2
    assert result.missing_count == 392
    assert report.total_missing_images == 392


@pytest.mark.asyncio
@respx.mock
async def test_never_downloaded_batch_is_missing():
    respx.get(f"{BASE}/arkis!A2/manifest").mock(
        return_value=httpx.Response(200, json=_manifest("A2", 10))
    )
    report = await verify_batches(["A2"], set(), base_url=BASE, workers=4)

    assert len(report.missing) == 1
    assert report.missing[0].state is BatchState.missing
    assert report.missing[0].missing_count == 10
    assert report.deficient == report.missing


@pytest.mark.asyncio
@respx.mock
async def test_manifest_fetch_failure_is_fetch_error_not_deficient():
    respx.get(f"{BASE}/arkis!BAD/manifest").mock(return_value=httpx.Response(500))
    report = await verify_batches(["BAD"], set(), base_url=BASE, workers=4, attempts=1)

    assert len(report.fetch_errors) == 1
    assert report.fetch_errors[0].expected is None
    # A fetch error is not counted as a recoverable deficiency.
    assert report.deficient == []


@pytest.mark.asyncio
@respx.mock
async def test_report_partitions_a_mixed_set():
    respx.get(f"{BASE}/arkis!OK/manifest").mock(
        return_value=httpx.Response(200, json=_manifest("OK", 5))
    )
    respx.get(f"{BASE}/arkis!SHORT/manifest").mock(
        return_value=httpx.Response(200, json=_manifest("SHORT", 100))
    )
    done = _done("OK", 5) | _done("SHORT", 90)
    report = await verify_batches(["OK", "SHORT"], done, base_url=BASE, workers=4)

    assert len(report.complete) == 1
    assert len(report.short) == 1
    assert report.total_missing_images == 10
