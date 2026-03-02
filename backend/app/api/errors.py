"""Common response helpers for route handlers."""

from __future__ import annotations

import logging

from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError, ReadTimeoutError
from fastapi import HTTPException
import httpx

logger = logging.getLogger(__name__)


def raise_for_s3_error(exc: ClientError, resource: str = "resource") -> None:
    """Translate a botocore ClientError into an HTTPException."""
    error = exc.response.get("Error", {})
    code = error.get("Code", "Unknown")
    message = error.get("Message", str(exc))
    status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 502)

    mapping = {
        "NoSuchBucket": 404,
        "NoSuchKey": 404,
        "BucketNotEmpty": 409,
        "BucketAlreadyExists": 409,
        "BucketAlreadyOwnedByYou": 409,
        "AccessDenied": 403,
        "InvalidBucketName": 400,
        "InvalidArgument": 400,
    }
    http_status = mapping.get(code, status)
    raise HTTPException(status_code=http_status, detail=f"{resource}: {message}")


def raise_for_s3_transport_error(exc: BotoCoreError, resource: str = "resource") -> None:
    """Translate a botocore transport/connection error into an HTTPException."""
    logger.error("S3 transport error for %s: %s", resource, exc)
    if isinstance(exc, EndpointConnectionError):
        raise HTTPException(status_code=502, detail=f"{resource}: S3 endpoint unreachable")
    if isinstance(exc, ReadTimeoutError):
        raise HTTPException(status_code=504, detail=f"{resource}: S3 read timed out")
    raise HTTPException(status_code=502, detail=f"{resource}: S3 connection error")


def raise_for_hcp_status(resp: httpx.Response, resource: str = "resource") -> None:
    """Translate HCP status codes into FastAPI HTTP exceptions."""
    code = resp.status_code
    if 200 <= code < 300:
        return

    detail = resp.headers.get("X-HCP-ErrorMessage", resp.text or f"HCP returned {code}")

    mapping = {
        302: (404, f"{resource} not found or no permission"),
        400: (400, detail),
        401: (502, "HCP unable to handle request"),
        403: (403, detail),
        404: (404, f"{resource} not found"),
        405: (405, "Method not allowed for this resource"),
        409: (409, f"{resource} already exists"),
        414: (414, "Request URI too large"),
        415: (415, "Unsupported media type"),
        500: (502, f"HCP internal error: {detail}"),
        503: (503, f"HCP unavailable: {detail}"),
    }

    status, msg = mapping.get(code, (502, f"Unexpected HCP status {code}: {detail}"))
    raise HTTPException(status_code=status, detail=msg)


def parse_json_response(resp: httpx.Response) -> dict:
    """Parse JSON response body, returning empty dict on empty body."""
    if 200 <= resp.status_code < 300 and resp.content:
        try:
            return resp.json()
        except (ValueError, TypeError):
            return {}
    return {}
