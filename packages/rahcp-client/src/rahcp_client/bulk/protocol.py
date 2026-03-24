"""Protocols for the bulk transfer engine — defines the S3 interface it needs."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class S3Client(Protocol):
    """Minimal S3 interface required by the bulk transfer engine."""

    async def head(self, bucket: str, key: str) -> dict: ...
    async def upload(self, bucket: str, key: str, data: Path) -> str: ...
    async def download(self, bucket: str, key: str, dest: Path) -> int: ...
    async def presign_put(
        self, bucket: str, key: str, *, expires: int = 3600
    ) -> str: ...
    async def presign_get(
        self, bucket: str, key: str, *, expires: int = 3600
    ) -> str: ...
    async def presign_bulk(
        self,
        bucket: str,
        keys: list[str],
        *,
        method: str = "get_object",
        expires: int = 3600,
    ) -> dict[str, str]: ...
    async def list_objects(
        self,
        bucket: str,
        prefix: str,
        *,
        max_keys: int = 1000,
        continuation_token: str | None = None,
    ) -> dict: ...


class BulkClient(Protocol):
    """Client that exposes an ``s3`` property satisfying :class:`S3Client`."""

    @property
    def s3(self) -> S3Client: ...
