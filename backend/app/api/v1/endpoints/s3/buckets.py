"""S3 bucket CRUD endpoints."""

from __future__ import annotations

import asyncio

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_s3_service
from app.api.errors import raise_for_s3_error, raise_for_s3_transport_error
from app.schemas.s3 import (
    AclPolicy,
    AclResponse,
    BucketInfo,
    BucketMutationResponse,
    BucketVersioningResponse,
    CreateBucketRequest,
    ListBucketsResponse,
    PutBucketVersioningRequest,
    VersioningMutationResponse,
)
from app.services.s3_service import S3Service

router = APIRouter(prefix="/buckets", tags=["S3 Buckets"])


@router.get("", response_model=ListBucketsResponse)
async def list_buckets(s3: S3Service = Depends(get_s3_service)):
    try:
        result = await asyncio.to_thread(s3.list_buckets)
    except ClientError as exc:
        raise_for_s3_error(exc, "buckets")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, "buckets")
    buckets = [BucketInfo.model_validate(b) for b in result.get("Buckets", [])]
    return ListBucketsResponse(buckets=buckets)


@router.post("", response_model=BucketMutationResponse, status_code=201)
async def create_bucket(
    body: CreateBucketRequest,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(s3.create_bucket, body.bucket)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{body.bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{body.bucket}'")
    return {"status": "created", "bucket": body.bucket}


@router.head("/{bucket}")
async def head_bucket(bucket: str, s3: S3Service = Depends(get_s3_service)):
    try:
        await asyncio.to_thread(s3.head_bucket, bucket)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{bucket}'")
    return Response(status_code=200)


@router.delete("/{bucket}", response_model=BucketMutationResponse)
async def delete_bucket(bucket: str, s3: S3Service = Depends(get_s3_service)):
    try:
        await asyncio.to_thread(s3.delete_bucket, bucket)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{bucket}'")
    return {"status": "deleted", "bucket": bucket}


# ── Bucket versioning ────────────────────────────────────────────────


@router.get("/{bucket}/versioning", response_model=BucketVersioningResponse)
async def get_bucket_versioning(
    bucket: str,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        result = await asyncio.to_thread(s3.get_bucket_versioning, bucket)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{bucket}'")
    return BucketVersioningResponse(
        status=result.get("Status"),
        mfa_delete=result.get("MFADelete"),
    )


@router.put("/{bucket}/versioning", response_model=VersioningMutationResponse)
async def put_bucket_versioning(
    bucket: str,
    body: PutBucketVersioningRequest,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(s3.put_bucket_versioning, bucket, body.status)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{bucket}'")
    return {"status": "updated", "versioning": body.status}


# ── Bucket ACL ────────────────────────────────────────────────────────


@router.get("/{bucket}/acl", response_model=AclResponse)
async def get_bucket_acl(bucket: str, s3: S3Service = Depends(get_s3_service)):
    try:
        result = await asyncio.to_thread(s3.get_bucket_acl, bucket)
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{bucket}'")
    return {
        "owner": result.get("Owner", {}),
        "grants": result.get("Grants", []),
    }


@router.put("/{bucket}/acl", response_model=BucketMutationResponse)
async def put_bucket_acl(
    bucket: str,
    body: AclPolicy,
    s3: S3Service = Depends(get_s3_service),
):
    try:
        await asyncio.to_thread(
            s3.put_bucket_acl, bucket, body.model_dump(exclude_none=True)
        )
    except ClientError as exc:
        raise_for_s3_error(exc, f"bucket '{bucket}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"bucket '{bucket}'")
    return {"status": "updated"}
