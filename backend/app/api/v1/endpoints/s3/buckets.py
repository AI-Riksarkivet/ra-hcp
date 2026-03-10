"""S3 bucket CRUD endpoints.

Endpoints:
    GET  /buckets              — list all buckets
    POST /buckets              — create a bucket
    HEAD /buckets/{bucket}     — check if bucket exists
    DELETE /buckets/{bucket}   — delete a bucket
    GET  /buckets/{bucket}/versioning — get versioning status
    PUT  /buckets/{bucket}/versioning — set versioning
    GET  /buckets/{bucket}/acl — get bucket ACL
    PUT  /buckets/{bucket}/acl — set bucket ACL
"""

from __future__ import annotations

import asyncio

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_s3_service
from app.api.errors import raise_for_s3_error, raise_for_s3_transport_error, run_s3
from app.schemas.s3 import (
    AclPolicy,
    AclResponse,
    BucketInfo,
    BucketMutationResponse,
    BucketVersioningResponse,
    CreateBucketRequest,
    ListBucketsResponse,
    OwnerInfo,
    PutBucketVersioningRequest,
    VersioningMutationResponse,
)
from app.services.storage import StorageProtocol

router = APIRouter(prefix="/buckets", tags=["S3 Buckets"])


@router.get("", response_model=ListBucketsResponse)
async def list_buckets(s3: StorageProtocol = Depends(get_s3_service)):
    """List all S3 buckets accessible to the authenticated user."""
    try:
        result = await asyncio.to_thread(s3.list_buckets)
    except ClientError as exc:
        raise_for_s3_error(exc, "buckets")
    except (BotoCoreError, TypeError) as exc:
        # TypeError: boto3 S3RegionRedirector passes bucket=None to
        # head_bucket when HCP returns a redirect-like status on
        # list_buckets (which has no bucket). This is a boto3/HCP
        # compatibility issue.
        raise_for_s3_transport_error(exc, "buckets")
    buckets = [BucketInfo.model_validate(b) for b in result.get("Buckets", [])]
    owner = OwnerInfo.model_validate(result["Owner"]) if "Owner" in result else None
    return ListBucketsResponse(buckets=buckets, owner=owner)


@router.post("", response_model=BucketMutationResponse, status_code=201)
async def create_bucket(
    body: CreateBucketRequest,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Create a new S3 bucket."""
    await run_s3(s3.create_bucket, f"bucket '{body.bucket}'", body.bucket)
    return {"status": "created", "bucket": body.bucket}


@router.head("/{bucket}")
async def head_bucket(bucket: str, s3: StorageProtocol = Depends(get_s3_service)):
    """Check whether a bucket exists. Returns 200 or 404."""
    await run_s3(s3.head_bucket, f"bucket '{bucket}'", bucket)
    return Response(status_code=200)


@router.delete("/{bucket}", response_model=BucketMutationResponse)
async def delete_bucket(bucket: str, s3: StorageProtocol = Depends(get_s3_service)):
    """Delete an S3 bucket. The bucket must be empty."""
    await run_s3(s3.delete_bucket, f"bucket '{bucket}'", bucket)
    return {"status": "deleted", "bucket": bucket}


# ── Bucket versioning ────────────────────────────────────────────────


@router.get("/{bucket}/versioning", response_model=BucketVersioningResponse)
async def get_bucket_versioning(
    bucket: str,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Get the versioning configuration for a bucket."""
    result = await run_s3(s3.get_bucket_versioning, f"bucket '{bucket}'", bucket)
    return BucketVersioningResponse(
        status=result.get("Status"),
        mfa_delete=result.get("MFADelete"),
    )


@router.put("/{bucket}/versioning", response_model=VersioningMutationResponse)
async def put_bucket_versioning(
    bucket: str,
    body: PutBucketVersioningRequest,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Enable or suspend versioning on a bucket."""
    await run_s3(s3.put_bucket_versioning, f"bucket '{bucket}'", bucket, body.status)
    return {"status": "updated", "versioning": body.status}


# ── Bucket ACL ────────────────────────────────────────────────────────


@router.get("/{bucket}/acl", response_model=AclResponse)
async def get_bucket_acl(bucket: str, s3: StorageProtocol = Depends(get_s3_service)):
    """Get the access control list (ACL) for a bucket."""
    result = await run_s3(s3.get_bucket_acl, f"bucket '{bucket}'", bucket)
    return {
        "owner": result.get("Owner", {}),
        "grants": result.get("Grants", []),
    }


@router.put("/{bucket}/acl", response_model=BucketMutationResponse)
async def put_bucket_acl(
    bucket: str,
    body: AclPolicy,
    s3: StorageProtocol = Depends(get_s3_service),
):
    """Set the access control list (ACL) for a bucket."""
    await run_s3(
        s3.put_bucket_acl,
        f"bucket '{bucket}'",
        bucket,
        body.model_dump(exclude_none=True),
    )
    return {"status": "updated"}
