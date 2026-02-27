"""S3 object CRUD endpoints."""

from __future__ import annotations

import asyncio
from typing import Optional

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_s3_service
from app.api.errors import raise_for_s3_error
from app.schemas.s3 import (
    CopyObjectRequest,
    DeleteObjectsRequest,
    HeadObjectResponse,
    ListObjectsResponse,
    ObjectInfo,
    UploadObjectResponse,
)
from app.services.s3_service import S3Service

router = APIRouter(prefix="/buckets/{bucket}/objects", tags=["S3 Objects"])


@router.get("")
async def list_objects(
    bucket: str,
    prefix: Optional[str] = Query(None),
    max_keys: int = Query(1000, le=1000),
    continuation_token: Optional[str] = Query(None),
    s3: S3Service = Depends(get_s3_service),
):
    try:
        result = await asyncio.to_thread(
            s3.list_objects, bucket, prefix, max_keys, continuation_token,
        )
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    objects = [ObjectInfo.model_validate(o) for o in result.get("Contents", [])]
    return ListObjectsResponse(
        objects=objects,
        is_truncated=result.get("IsTruncated", False),
        next_continuation_token=result.get("NextContinuationToken"),
        key_count=result.get("KeyCount", 0),
    )


# ── Bulk delete (must be before {key:path} catch-all) ────────────────

@router.post("/delete")
async def delete_objects(
    bucket: str,
    body: DeleteObjectsRequest,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        result = await asyncio.to_thread(s3.delete_objects, bucket, body.keys)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    return {
        "status": "deleted",
        "deleted": len(body.keys),
        "errors": result.get("Errors", []),
    }


# ── Routes with /acl suffix (must be before {key:path} catch-all) ───

@router.get("/{key:path}/acl")
async def get_object_acl(
    bucket: str, key: str, s3: S3Service = Depends(get_s3_service),
):
    try:
        result = await asyncio.to_thread(s3.get_object_acl, bucket, key)
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
    return {
        "owner": result.get("Owner", {}),
        "grants": result.get("Grants", []),
    }


@router.put("/{key:path}/acl")
async def put_object_acl(
    bucket: str, key: str, body: dict,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(s3.put_object_acl, bucket, key, body)
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
    return {"status": "updated"}


# ── Copy route (must be before {key:path} catch-all) ─────────────────

@router.post("/{key:path}/copy")
async def copy_object(
    bucket: str,
    key: str,
    body: CopyObjectRequest,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(
            s3.copy_object, body.source_bucket, body.source_key, bucket, key,
        )
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
    return {"status": "copied", "bucket": bucket, "key": key}


# ── Single-object CRUD ({key:path} catch-all routes last) ────────────

@router.post("/{key:path}", response_model=UploadObjectResponse)
async def upload_object(
    bucket: str,
    key: str,
    file: UploadFile = File(...),
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(s3.put_object, bucket, key, file.file)
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
    return UploadObjectResponse(bucket=bucket, key=key)


@router.get("/{key:path}")
async def download_object(
    bucket: str,
    key: str,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        result = await asyncio.to_thread(s3.get_object, bucket, key)
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
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
    try:
        result = await asyncio.to_thread(s3.head_object, bucket, key)
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
    return HeadObjectResponse(
        content_length=result.get("ContentLength"),
        content_type=result.get("ContentType"),
        etag=result.get("ETag"),
        last_modified=str(result.get("LastModified", "")),
    )


@router.delete("/{key:path}")
async def delete_object(
    bucket: str,
    key: str,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(s3.delete_object, bucket, key)
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{key}'")
    return {"status": "deleted", "bucket": bucket, "key": key}
