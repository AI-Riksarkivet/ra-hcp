"""S3 object CRUD endpoints."""

from __future__ import annotations

import asyncio
import io
import zipfile
from typing import Optional

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_s3_service
from app.api.errors import run_s3
from app.schemas.s3 import (
    AclPolicy,
    AclResponse,
    BulkDownloadRequest,
    BulkPresignRequest,
    BulkPresignResponse,
    CopyObjectRequest,
    DeleteObjectsRequest,
    DeleteObjectsResponse,
    HeadObjectResponse,
    ListObjectsResponse,
    ObjectInfo,
    ObjectMutationResponse,
    UploadObjectResponse,
)
from app.schemas.common import StatusResponse
from app.services.s3_service import S3Service

router = APIRouter(prefix="/buckets/{bucket}/objects", tags=["S3 Objects"])


@router.get("", response_model=ListObjectsResponse)
async def list_objects(
    bucket: str,
    prefix: Optional[str] = Query(None),
    max_keys: int = Query(1000, le=1000),
    continuation_token: Optional[str] = Query(None),
    delimiter: Optional[str] = Query(None),
    s3: S3Service = Depends(get_s3_service),
):
    result = await run_s3(
        s3.list_objects,
        f"bucket '{bucket}'",
        bucket,
        prefix,
        max_keys,
        continuation_token,
        delimiter,
    )
    objects = [ObjectInfo.model_validate(o) for o in result.get("Contents", [])]
    common_prefixes = [
        cp["Prefix"] for cp in result.get("CommonPrefixes", []) if "Prefix" in cp
    ]
    return ListObjectsResponse(
        objects=objects,
        common_prefixes=common_prefixes,
        is_truncated=result.get("IsTruncated", False),
        next_continuation_token=result.get("NextContinuationToken"),
        key_count=result.get("KeyCount", 0),
    )


# ── Bulk delete (must be before {key:path} catch-all) ────────────────


@router.post("/delete", response_model=DeleteObjectsResponse)
async def delete_objects(
    bucket: str,
    body: DeleteObjectsRequest,
    s3: S3Service = Depends(get_s3_service),
):
    result = await run_s3(s3.delete_objects, f"bucket '{bucket}'", bucket, body.keys)
    return {
        "status": "deleted",
        "deleted": len(body.keys),
        "errors": result.get("Errors", []),
    }


# ── Bulk download (must be before {key:path} catch-all) ──────────────


@router.post("/download")
async def download_objects(
    bucket: str,
    body: BulkDownloadRequest,
    s3: S3Service = Depends(get_s3_service),
):
    async def _generate_zip():
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for key in body.keys:
                try:
                    result = await asyncio.to_thread(s3.get_object, bucket, key)
                    data = result["Body"].read()
                    zf.writestr(key, data)
                except (ClientError, BotoCoreError):
                    continue
        buf.seek(0)
        yield buf.read()

    return StreamingResponse(
        content=_generate_zip(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{bucket}-objects.zip"',
        },
    )


# ── Bulk presign (must be before {key:path} catch-all) ───────────────


@router.post("/presign", response_model=BulkPresignResponse)
async def bulk_presign(
    bucket: str,
    body: BulkPresignRequest,
    s3: S3Service = Depends(get_s3_service),
):
    urls = []
    for key in body.keys:
        try:
            url = await asyncio.to_thread(
                s3.generate_presigned_url, bucket, key, body.expires_in
            )
            urls.append({"key": key, "url": url})
        except (ClientError, BotoCoreError):
            continue
    return BulkPresignResponse(urls=urls, expires_in=body.expires_in)


# ── Routes with /acl suffix (must be before {key:path} catch-all) ───


@router.get("/{key:path}/acl", response_model=AclResponse)
async def get_object_acl(
    bucket: str,
    key: str,
    s3: S3Service = Depends(get_s3_service),
):
    result = await run_s3(s3.get_object_acl, f"object '{key}'", bucket, key)
    return {
        "owner": result.get("Owner", {}),
        "grants": result.get("Grants", []),
    }


@router.put("/{key:path}/acl", response_model=StatusResponse)
async def put_object_acl(
    bucket: str,
    key: str,
    body: AclPolicy,
    s3: S3Service = Depends(get_s3_service),
):
    await run_s3(
        s3.put_object_acl,
        f"object '{key}'",
        bucket,
        key,
        body.model_dump(exclude_none=True),
    )
    return {"status": "updated"}


# ── Copy route (must be before {key:path} catch-all) ─────────────────


@router.post("/{key:path}/copy", response_model=ObjectMutationResponse)
async def copy_object(
    bucket: str,
    key: str,
    body: CopyObjectRequest,
    s3: S3Service = Depends(get_s3_service),
):
    await run_s3(
        s3.copy_object,
        f"object '{key}'",
        body.source_bucket,
        body.source_key,
        bucket,
        key,
    )
    return ObjectMutationResponse(status="copied", bucket=bucket, key=key)


# ── Single-object CRUD ({key:path} catch-all routes last) ────────────


@router.post("/{key:path}", response_model=UploadObjectResponse, status_code=201)
async def upload_object(
    bucket: str,
    key: str,
    file: UploadFile = File(...),
    s3: S3Service = Depends(get_s3_service),
):
    await run_s3(s3.put_object, f"object '{key}'", bucket, key, file.file)
    return UploadObjectResponse(bucket=bucket, key=key)


@router.get("/{key:path}")
async def download_object(
    bucket: str,
    key: str,
    s3: S3Service = Depends(get_s3_service),
):
    result = await run_s3(s3.get_object, f"object '{key}'", bucket, key)
    body = result["Body"]
    return StreamingResponse(
        content=body.iter_chunks(),
        media_type=result.get("ContentType", "application/octet-stream"),
        headers={
            "Content-Length": str(result.get("ContentLength", "")),
            "ETag": result.get("ETag", ""),
        },
    )


@router.head("/{key:path}", response_model=HeadObjectResponse)
async def head_object(
    bucket: str,
    key: str,
    s3: S3Service = Depends(get_s3_service),
):
    result = await run_s3(s3.head_object, f"object '{key}'", bucket, key)
    return HeadObjectResponse(
        content_length=result.get("ContentLength"),
        content_type=result.get("ContentType"),
        etag=result.get("ETag"),
        last_modified=str(result.get("LastModified", "")),
    )


@router.delete("/{key:path}", response_model=ObjectMutationResponse)
async def delete_object(
    bucket: str,
    key: str,
    s3: S3Service = Depends(get_s3_service),
):
    await run_s3(s3.delete_object, f"object '{key}'", bucket, key)
    return ObjectMutationResponse(status="deleted", bucket=bucket, key=key)
