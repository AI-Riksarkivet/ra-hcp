"""End-to-end S3 tests against a *real* moto server (ThreadedMotoServer).

``test_moto_integration.py`` is skipped because moto's ``mock_aws`` decorator
patches sync botocore and breaks aiobotocore (async responses).  ThreadedMotoServer
instead runs a real HTTP S3 endpoint, so the GenericBoto3 adapter's real aioboto3
client talks to it normally — exercising the full async call path, including the
presign -> real HTTP PUT/GET round trip that the rahcp SDK's ``s3.upload`` relies on.
"""

from __future__ import annotations

import io
import socket

import httpx
import pytest
from moto.server import ThreadedMotoServer
from pydantic import SecretStr

from app.core.config import StorageSettings
from app.services.storage.adapters.generic_boto3 import GenericBoto3Storage
from app.services.storage.errors import StorageError

pytestmark = pytest.mark.moto

BUCKET = "e2e-bucket"
REGION = "us-east-1"


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture
def moto_server():
    """A real in-process S3 server. Fresh per test for isolation."""
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=_free_port())
    server.start()
    host, port = server.get_host_and_port()
    base = f"http://{host}:{port}"
    # moto's in-memory backends are process-global — wipe state from a prior test.
    httpx.post(f"{base}/moto-api/reset")
    yield base
    server.stop()


@pytest.fixture
async def storage(moto_server: str):
    """A connected GenericBoto3Storage adapter pointed at the moto server."""
    settings = StorageSettings(
        storage_backend="generic",
        s3_endpoint_url=moto_server,
        s3_region=REGION,
        s3_addressing_style="path",  # path style so presigned URLs hit 127.0.0.1:PORT/bucket/key
        s3_access_key="testing",
        s3_secret_key=SecretStr("testing"),
        s3_verify_ssl=False,
    )
    store = GenericBoto3Storage.with_credentials(
        settings, "testing", "testing", endpoint_url=moto_server
    )
    await store.connect()
    await store.create_bucket(BUCKET)
    yield store
    await store.close()


async def test_put_get_head_roundtrip(storage: GenericBoto3Storage):
    await storage.put_object(BUCKET, "hello.txt", io.BytesIO(b"Hello, world!"))

    got = await storage.get_object(BUCKET, "hello.txt")
    assert await got["Body"].read() == b"Hello, world!"

    head = await storage.head_object(BUCKET, "hello.txt")
    assert head["ContentLength"] == len(b"Hello, world!")


async def test_list_objects_with_prefix(storage: GenericBoto3Storage):
    await storage.put_object(BUCKET, "docs/a.txt", io.BytesIO(b"a"))
    await storage.put_object(BUCKET, "docs/b.txt", io.BytesIO(b"b"))
    await storage.put_object(BUCKET, "img/c.png", io.BytesIO(b"c"))

    res = await storage.list_objects(BUCKET, prefix="docs/")
    keys = {obj["Key"] for obj in res.get("Contents", [])}
    assert keys == {"docs/a.txt", "docs/b.txt"}


async def test_presigned_put_then_get_over_real_http(storage: GenericBoto3Storage):
    """The crux: presign PUT, upload over real HTTP, then download and verify.

    This is exactly the path the rahcp SDK uses for ``s3.upload(bucket, key, bytes)``.
    """
    data = b"\xff\xd8presigned-image-bytes\xff\xd9"
    key = "scan/0001.jpg"

    put_url = await storage.generate_presigned_url(BUCKET, key, 300, "put_object")
    async with httpx.AsyncClient() as http:
        put_resp = await http.put(put_url, content=data)
    assert put_resp.status_code in (200, 204)

    # Visible through the adapter...
    got = await storage.get_object(BUCKET, key)
    assert await got["Body"].read() == data

    # ...and downloadable via a presigned GET over real HTTP.
    get_url = await storage.generate_presigned_url(BUCKET, key, 300, "get_object")
    async with httpx.AsyncClient() as http:
        get_resp = await http.get(get_url)
    assert get_resp.status_code == 200
    assert get_resp.content == data


async def test_delete_object_then_get_raises(storage: GenericBoto3Storage):
    await storage.put_object(BUCKET, "temp.txt", io.BytesIO(b"temp"))
    await storage.delete_object(BUCKET, "temp.txt")

    with pytest.raises(StorageError) as exc_info:
        await storage.get_object(BUCKET, "temp.txt")
    assert exc_info.value.code == "NoSuchKey"


async def test_multipart_upload_assembles_parts(storage: GenericBoto3Storage):
    init = await storage.create_multipart_upload(BUCKET, "big.bin")
    upload_id = init["UploadId"]

    part1 = await storage.upload_part(
        BUCKET, "big.bin", upload_id, 1, io.BytesIO(b"A" * 5 * 1024 * 1024)
    )
    part2 = await storage.upload_part(
        BUCKET, "big.bin", upload_id, 2, io.BytesIO(b"B" * 1024 * 1024)
    )
    await storage.complete_multipart_upload(
        BUCKET,
        "big.bin",
        upload_id,
        [
            {"PartNumber": 1, "ETag": part1["ETag"]},
            {"PartNumber": 2, "ETag": part2["ETag"]},
        ],
    )

    got = await storage.get_object(BUCKET, "big.bin")
    body = await got["Body"].read()
    assert len(body) == 6 * 1024 * 1024
