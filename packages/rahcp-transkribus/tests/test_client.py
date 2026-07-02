"""Unit tests for the async Transkribus REST client."""

from __future__ import annotations

import httpx
import pytest
import respx

from rahcp_transkribus import TranskribusAuthError, TranskribusClient
from rahcp_transkribus.client import _extract_session_id

BASE = "https://transkribus.eu/TrpServer/rest"

LOGIN_XML = "<trpUserLogin><sessionId>SESSION123</sessionId></trpUserLogin>"


def _mock_auth(router: respx.Router) -> None:
    router.post(f"{BASE}/auth/login").mock(
        return_value=httpx.Response(200, text=LOGIN_XML)
    )
    router.post(f"{BASE}/auth/logout").mock(return_value=httpx.Response(200))


def test_extract_session_id_namespace_agnostic():
    xml = '<ns:root xmlns:ns="urn:x"><ns:sessionId>ABC</ns:sessionId></ns:root>'
    assert _extract_session_id(xml) == "ABC"


def test_extract_session_id_missing_raises():
    with pytest.raises(TranskribusAuthError, match="no sessionId"):
        _extract_session_id("<trpUserLogin></trpUserLogin>")


@respx.mock
async def test_login_sets_session_cookie():
    _mock_auth(respx.mock)
    async with TranskribusClient("user@example.se", "pw") as client:
        assert client.session_id == "SESSION123"
        assert client._client.cookies.get("JSESSIONID") == "SESSION123"


@respx.mock
async def test_login_bad_credentials_raises_auth_error():
    respx.post(f"{BASE}/auth/login").mock(return_value=httpx.Response(401))
    with pytest.raises(TranskribusAuthError, match="invalid Transkribus credentials"):
        async with TranskribusClient("user", "wrong"):
            pass


@respx.mock
async def test_failed_login_closes_client_no_leak():
    """A login failure inside __aenter__ must close the httpx client (no leak)."""
    respx.post(f"{BASE}/auth/login").mock(return_value=httpx.Response(401))
    client = TranskribusClient("user", "wrong")
    with pytest.raises(TranskribusAuthError):
        await client.__aenter__()
    assert client._client is None


@respx.mock
async def test_list_docs_parses_documents():
    _mock_auth(respx.mock)
    route = respx.get(f"{BASE}/collections/42/list").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"docId": 1, "title": "Doc One", "nrOfPages": 3},
                {"docId": 2, "title": "Doc Two"},
            ],
        )
    )
    async with TranskribusClient("u", "p") as client:
        docs = await client.list_docs(42)

    assert [d.doc_id for d in docs] == [1, 2]
    assert docs[0].title == "Doc One"
    assert docs[0].nr_of_pages == 3
    # index=0, nValues=0 requests the whole collection
    assert route.calls.last.request.url.params["nValues"] == "0"


@respx.mock
async def test_get_pages_forwards_status_filter():
    _mock_auth(respx.mock)
    route = respx.get(f"{BASE}/collections/42/7/pages").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "pageNr": 1,
                    "url": "https://files.example/img1.jpg",
                    "imgFileName": "0001.jpg",
                    "tsList": {
                        "transcripts": [
                            {
                                "fileName": "0001.xml",
                                "url": "https://files.example/ts1.xml",
                                "status": "GT",
                                "tsId": 111,
                            }
                        ]
                    },
                }
            ],
        )
    )
    async with TranskribusClient("u", "p") as client:
        pages = await client.get_pages(
            42, 7, status="GT", skip_pages_with_missing_status=True
        )

    assert len(pages) == 1
    assert pages[0].page_nr == 1
    assert pages[0].img_file_name == "0001.jpg"
    assert pages[0].ts_list.transcripts[0].file_name == "0001.xml"
    params = route.calls.last.request.url.params
    assert params["status"] == "GT"
    assert params["skipPagesWithMissingStatus"] == "true"


@respx.mock
async def test_request_retries_transient_status():
    _mock_auth(respx.mock)
    route = respx.get(f"{BASE}/collections/1/list").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json=[{"docId": 9, "title": "Recovered"}]),
        ]
    )
    async with TranskribusClient("u", "p", retry_base_delay=0.0) as client:
        docs = await client.list_docs(1)

    assert route.call_count == 2
    assert docs[0].doc_id == 9


@respx.mock
async def test_fetch_bytes_returns_content():
    _mock_auth(respx.mock)
    respx.get("https://files.example/img1.jpg").mock(
        return_value=httpx.Response(200, content=b"\xff\xd8jpegbytes")
    )
    async with TranskribusClient("u", "p") as client:
        data = await client.fetch_bytes("https://files.example/img1.jpg")

    assert data == b"\xff\xd8jpegbytes"


async def test_client_methods_require_context_manager():
    from rahcp_transkribus.errors import TranskribusError

    client = TranskribusClient("u", "p")
    with pytest.raises(TranskribusError, match="async context manager"):
        await client.list_docs(1)
