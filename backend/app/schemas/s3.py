"""S3 request/response schemas."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateBucketRequest(BaseModel):
    bucket: str


class BucketInfo(BaseModel):
    name: str = Field(alias="Name")
    creation_date: Optional[datetime] = Field(None, alias="CreationDate")

    model_config = {"populate_by_name": True}


class ListBucketsResponse(BaseModel):
    buckets: List[BucketInfo] = []


class ObjectInfo(BaseModel):
    key: str = Field(alias="Key")
    size: Optional[int] = Field(None, alias="Size")
    last_modified: Optional[datetime] = Field(None, alias="LastModified")
    etag: Optional[str] = Field(None, alias="ETag")
    storage_class: Optional[str] = Field(None, alias="StorageClass")

    model_config = {"populate_by_name": True}


class ListObjectsResponse(BaseModel):
    objects: List[ObjectInfo] = []
    is_truncated: bool = False
    next_continuation_token: Optional[str] = None
    key_count: int = 0


class UploadObjectResponse(BaseModel):
    bucket: str
    key: str
    status: str = "uploaded"


class HeadObjectResponse(BaseModel):
    content_length: Optional[int] = None
    content_type: Optional[str] = None
    etag: Optional[str] = None
    last_modified: Optional[str] = None


class CopyObjectRequest(BaseModel):
    source_bucket: str
    source_key: str


class DeleteObjectsRequest(BaseModel):
    keys: List[str]


class BucketVersioningResponse(BaseModel):
    status: Optional[str] = None
    mfa_delete: Optional[str] = None


class PutBucketVersioningRequest(BaseModel):
    status: str = Field(..., description="Enabled or Suspended")


# ── ACL Models ────────────────────────────────────────────────────────


class AclOwner(BaseModel):
    model_config = {"extra": "allow"}

    ID: Optional[str] = None
    DisplayName: Optional[str] = None


class AclGrant(BaseModel):
    model_config = {"extra": "allow"}

    Grantee: Optional[dict] = None
    Permission: Optional[str] = None


class AclPolicy(BaseModel):
    """S3 ACL policy for buckets and objects."""

    model_config = {"extra": "allow"}

    Owner: Optional[AclOwner] = None
    Grants: Optional[List[AclGrant]] = None


class AclResponse(BaseModel):
    """Response for GET bucket/object ACL."""

    owner: Optional[dict] = None
    grants: Optional[List[dict]] = None


# ── Mutation Response Models ─────────────────────────────────────────


class BucketMutationResponse(BaseModel):
    """Response for bucket create/delete."""

    status: str
    bucket: Optional[str] = None


class VersioningMutationResponse(BaseModel):
    """Response for PUT bucket versioning."""

    status: str
    versioning: Optional[str] = None


class ObjectMutationResponse(BaseModel):
    """Response for object copy/delete."""

    status: str
    bucket: Optional[str] = None
    key: Optional[str] = None


class DeleteObjectsResponse(BaseModel):
    """Response for bulk delete."""

    status: str
    deleted: int
    errors: Optional[List[dict]] = None


# ── Presigned URL Models ─────────────────────────────────────────


class PresignedUrlRequest(BaseModel):
    """Request body for generating a presigned URL."""

    bucket: str
    key: str
    expires_in: int = Field(
        3600, ge=1, le=604800, description="Expiry in seconds (max 7 days)"
    )
    method: str = Field(
        "get_object", description="get_object for download, put_object for upload"
    )


class PresignedUrlResponse(BaseModel):
    """Response containing the generated presigned URL."""

    url: str
    bucket: str
    key: str
    expires_in: int
    method: str


# ── S3 Credentials Model ────────────────────────────────────────


class S3CredentialsResponse(BaseModel):
    """HCP-derived S3 credentials for the authenticated user."""

    access_key_id: str
    secret_access_key: str
    username: str
    tenant: Optional[str] = None
    endpoint_url: Optional[str] = None
