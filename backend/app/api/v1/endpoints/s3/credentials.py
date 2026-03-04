"""S3 presigned URL generation and credential derivation endpoints."""

from __future__ import annotations

import asyncio
from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends

from app.api.dependencies import _derive_s3_keys, get_s3_service, get_s3_settings
from app.api.errors import raise_for_s3_error, raise_for_s3_transport_error
from app.core.security import (
    HcpCredentials,
    oauth2_scheme,
    verify_token_with_credentials,
)
from app.core.tenant_routing import s3_endpoint_for_tenant
from app.schemas.s3 import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    S3CredentialsResponse,
)
from app.services.s3_service import S3Service

router = APIRouter(tags=["S3 Credentials"])

_ALLOWED_METHODS = {"get_object", "put_object"}


@router.post("/presign", response_model=PresignedUrlResponse)
async def generate_presigned_url(
    body: PresignedUrlRequest,
    s3: S3Service = Depends(get_s3_service),
):
    """Generate a presigned URL for temporary access to an object.

    Use `get_object` to create a download link, or `put_object` for an upload link.
    The URL is valid for the specified duration (default 1 hour, max 7 days).
    Anyone with the URL can access the object — no credentials needed.
    """
    if body.method not in _ALLOWED_METHODS:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=422,
            detail=f"method must be one of: {', '.join(sorted(_ALLOWED_METHODS))}",
        )
    try:
        url = await asyncio.to_thread(
            s3.generate_presigned_url,
            body.bucket,
            body.key,
            body.expires_in,
            body.method,
        )
    except ClientError as exc:
        raise_for_s3_error(exc, f"object '{body.key}'")
    except BotoCoreError as exc:
        raise_for_s3_transport_error(exc, f"object '{body.key}'")
    return PresignedUrlResponse(
        url=url,
        bucket=body.bucket,
        key=body.key,
        expires_in=body.expires_in,
        method=body.method,
    )


@router.get("/credentials", response_model=S3CredentialsResponse)
async def get_s3_credentials(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    """Return the S3 Access Key ID and Secret Access Key for the authenticated user.

    HCP derives S3 credentials deterministically from your username and password:
    - **Access Key ID** = base64(username)
    - **Secret Access Key** = md5(password)

    These credentials are used with any S3-compatible client (boto3, aws-cli, etc.)
    to authenticate against HCP's S3 API.
    """
    creds: HcpCredentials = verify_token_with_credentials(token)
    access_key, secret_key = _derive_s3_keys(creds)
    settings = get_s3_settings()
    endpoint_url = s3_endpoint_for_tenant(creds.tenant, settings.hcp_domain)
    return S3CredentialsResponse(
        access_key_id=access_key,
        secret_access_key=secret_key,
        username=creds.username,
        tenant=creds.tenant,
        endpoint_url=endpoint_url,
    )
