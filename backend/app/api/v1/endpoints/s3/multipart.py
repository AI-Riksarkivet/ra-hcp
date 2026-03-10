"""S3 multipart upload endpoints.

Route ordering: specific suffix routes (/complete, /abort, /parts) must
come before the {key:path} catch-all routes to avoid being swallowed.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.dependencies import get_s3_service
from app.api.errors import run_s3
from app.schemas.common import StatusResponse
from app.schemas.s3 import (
    AbortMultipartUploadRequest,
    CompleteMultipartUploadRequest,
    CompleteMultipartUploadResponse,
    CreateMultipartUploadResponse,
    ListPartsResponse,
    PartInfo,
    UploadPartResponse,
)
from app.services.storage import StorageProtocol

router = APIRouter(
    prefix="/buckets/{bucket}/multipart",
    tags=["S3 Multipart Upload"],
)


# ── Specific suffix routes (must come before {key:path} catch-all) ───


@router.post("/{key:path}/complete", response_model=CompleteMultipartUploadResponse)
async def complete_multipart_upload(
    bucket: str,
    key: str,
    body: CompleteMultipartUploadRequest,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Complete a multipart upload by assembling uploaded parts."""
    result = await run_s3(
        s3.complete_multipart_upload,
        f"object '{key}'",
        bucket,
        key,
        body.upload_id,
        body.parts,
    )
    return CompleteMultipartUploadResponse(
        bucket=bucket,
        key=key,
        etag=result.get("ETag"),
    )


@router.post("/{key:path}/abort", response_model=StatusResponse)
async def abort_multipart_upload(
    bucket: str,
    key: str,
    body: AbortMultipartUploadRequest,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Abort a multipart upload and discard uploaded parts."""
    await run_s3(
        s3.abort_multipart_upload,
        f"object '{key}'",
        bucket,
        key,
        body.upload_id,
    )
    return StatusResponse(status="aborted")


@router.get("/{key:path}/parts", response_model=ListPartsResponse)
async def list_parts(
    bucket: str,
    key: str,
    upload_id: str = Query(...),
    max_parts: int = Query(1000, le=1000),
    s3: StorageProtocol = Depends(get_s3_service),
):
    """List uploaded parts for a multipart upload."""
    result = await run_s3(
        s3.list_parts,
        f"object '{key}'",
        bucket,
        key,
        upload_id,
        max_parts,
    )
    parts = [PartInfo.model_validate(p) for p in result.get("Parts", [])]
    return ListPartsResponse(
        bucket=bucket,
        key=key,
        upload_id=upload_id,
        parts=parts,
        is_truncated=result.get("IsTruncated", False),
    )


# ── Catch-all routes ({key:path} matches everything) ────────────────


@router.post(
    "/{key:path}", response_model=CreateMultipartUploadResponse, status_code=201
)
async def create_multipart_upload(
    bucket: str,
    key: str,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Initiate a multipart upload and return an upload ID."""
    result = await run_s3(s3.create_multipart_upload, f"object '{key}'", bucket, key)
    return CreateMultipartUploadResponse(
        bucket=bucket,
        key=key,
        upload_id=result["UploadId"],
    )


@router.put("/{key:path}", response_model=UploadPartResponse)
async def upload_part(
    bucket: str,
    key: str,
    upload_id: str = Query(...),
    part_number: int = Query(..., ge=1, le=10000),
    file: UploadFile = File(...),
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Upload a single part of a multipart upload."""
    result = await run_s3(
        s3.upload_part,
        f"object '{key}' part {part_number}",
        bucket,
        key,
        upload_id,
        part_number,
        file.file,
    )
    return UploadPartResponse(
        part_number=part_number,
        etag=result["ETag"],
    )
