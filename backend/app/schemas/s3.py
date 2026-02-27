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
