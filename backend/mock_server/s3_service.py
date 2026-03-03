"""In-memory S3 service for the mock development server."""

from __future__ import annotations

import hashlib
import io
import logging
from datetime import datetime, timezone
from typing import IO, Any, Dict, List, Optional


class _StoredObject:
    """Metadata + bytes for a single stored object."""

    __slots__ = ("data", "content_type", "etag", "last_modified")

    def __init__(self, data: bytes, content_type: str = "application/octet-stream"):
        self.data = data
        self.content_type = content_type
        self.etag = f'"{hashlib.md5(data).hexdigest()}"'
        self.last_modified = datetime.now(timezone.utc).isoformat()


class MockS3Service:
    """In-memory S3 service implementing the same interface as S3Service."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("mock_server.s3")
        # bucket_name -> metadata dict
        self._buckets: Dict[str, Dict[str, Any]] = {}
        # bucket_name -> {key -> _StoredObject}
        self._objects: Dict[str, Dict[str, _StoredObject]] = {}
        # bucket_name -> versioning status str
        self._versioning: Dict[str, str] = {}
        # bucket_name -> ACL dict
        self._bucket_acls: Dict[str, Dict[str, Any]] = {}
        # (bucket, key) -> ACL dict
        self._object_acls: Dict[tuple, Dict[str, Any]] = {}

    def _require_bucket(self, name: str) -> None:
        if name not in self._buckets:
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {
                        "Code": "NoSuchBucket",
                        "Message": f"Bucket '{name}' does not exist",
                    },
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "HeadBucket",
            )

    def _require_object(self, bucket: str, key: str) -> _StoredObject:
        self._require_bucket(bucket)
        obj = self._objects.get(bucket, {}).get(key)
        if obj is None:
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {
                        "Code": "NoSuchKey",
                        "Message": f"Object '{key}' not found",
                    },
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                "HeadObject",
            )
        return obj

    # ── Bucket operations ─────────────────────────────────────────────

    def list_buckets(self) -> dict:
        self._logger.info("list_buckets")
        buckets = [
            {"Name": name, "CreationDate": meta.get("CreationDate", "")}
            for name, meta in self._buckets.items()
        ]
        return {"Buckets": buckets}

    def create_bucket(self, name: str) -> dict:
        self._logger.info("create_bucket name=%s", name)
        if name in self._buckets:
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {
                        "Code": "BucketAlreadyOwnedByYou",
                        "Message": "Bucket already exists",
                    },
                    "ResponseMetadata": {"HTTPStatusCode": 409},
                },
                "CreateBucket",
            )
        self._buckets[name] = {"CreationDate": datetime.now(timezone.utc).isoformat()}
        self._objects[name] = {}
        return {}

    def head_bucket(self, name: str) -> dict:
        self._logger.info("head_bucket name=%s", name)
        self._require_bucket(name)
        return {}

    def delete_bucket(self, name: str) -> dict:
        self._logger.info("delete_bucket name=%s", name)
        self._require_bucket(name)
        if self._objects.get(name):
            from botocore.exceptions import ClientError

            raise ClientError(
                {
                    "Error": {
                        "Code": "BucketNotEmpty",
                        "Message": "Bucket is not empty",
                    },
                    "ResponseMetadata": {"HTTPStatusCode": 409},
                },
                "DeleteBucket",
            )
        del self._buckets[name]
        self._objects.pop(name, None)
        self._versioning.pop(name, None)
        self._bucket_acls.pop(name, None)
        return {}

    # ── Object operations ─────────────────────────────────────────────

    def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> dict:
        self._logger.info("list_objects bucket=%s prefix=%s", bucket, prefix)
        self._require_bucket(bucket)
        all_keys = sorted(self._objects.get(bucket, {}).keys())
        if prefix:
            all_keys = [k for k in all_keys if k.startswith(prefix)]

        start = 0
        if continuation_token:
            try:
                start = int(continuation_token)
            except ValueError:
                start = 0

        page = all_keys[start : start + max_keys]
        is_truncated = (start + max_keys) < len(all_keys)

        contents = []
        for key in page:
            obj = self._objects[bucket][key]
            contents.append(
                {
                    "Key": key,
                    "Size": len(obj.data),
                    "LastModified": obj.last_modified,
                    "ETag": obj.etag,
                    "StorageClass": "STANDARD",
                }
            )

        result: dict[str, Any] = {
            "Contents": contents,
            "IsTruncated": is_truncated,
            "KeyCount": len(contents),
        }
        if is_truncated:
            result["NextContinuationToken"] = str(start + max_keys)
        return result

    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None:
        self._logger.info("put_object bucket=%s key=%s", bucket, key)
        self._require_bucket(bucket)
        data = body.read()
        self._objects[bucket][key] = _StoredObject(data)

    def get_object(self, bucket: str, key: str) -> dict:
        self._logger.info("get_object bucket=%s key=%s", bucket, key)
        obj = self._require_object(bucket, key)
        body = io.BytesIO(obj.data)
        # Mimic boto3 streaming body with iter_chunks
        body.iter_chunks = lambda chunk_size=1024: iter([obj.data])  # type: ignore[attr-defined]
        return {
            "Body": body,
            "ContentType": obj.content_type,
            "ContentLength": len(obj.data),
            "ETag": obj.etag,
        }

    def head_object(self, bucket: str, key: str) -> dict:
        self._logger.info("head_object bucket=%s key=%s", bucket, key)
        obj = self._require_object(bucket, key)
        return {
            "ContentLength": len(obj.data),
            "ContentType": obj.content_type,
            "ETag": obj.etag,
            "LastModified": obj.last_modified,
        }

    def delete_object(self, bucket: str, key: str) -> dict:
        self._logger.info("delete_object bucket=%s key=%s", bucket, key)
        self._require_bucket(bucket)
        self._objects.get(bucket, {}).pop(key, None)
        self._object_acls.pop((bucket, key), None)
        return {}

    def copy_object(
        self,
        src_bucket: str,
        src_key: str,
        dst_bucket: str,
        dst_key: str,
    ) -> dict:
        self._logger.info(
            "copy_object %s/%s -> %s/%s", src_bucket, src_key, dst_bucket, dst_key
        )
        src_obj = self._require_object(src_bucket, src_key)
        self._require_bucket(dst_bucket)
        self._objects[dst_bucket][dst_key] = _StoredObject(
            src_obj.data,
            src_obj.content_type,
        )
        return {}

    def delete_objects(self, bucket: str, keys: List[str]) -> dict:
        self._logger.info("delete_objects bucket=%s count=%d", bucket, len(keys))
        self._require_bucket(bucket)
        deleted = []
        for key in keys:
            if key in self._objects.get(bucket, {}):
                del self._objects[bucket][key]
                self._object_acls.pop((bucket, key), None)
                deleted.append({"Key": key})
        return {"Deleted": deleted, "Errors": []}

    # ── Versioning ────────────────────────────────────────────────────

    def get_bucket_versioning(self, bucket: str) -> dict:
        self._logger.info("get_bucket_versioning bucket=%s", bucket)
        self._require_bucket(bucket)
        status = self._versioning.get(bucket)
        return {"Status": status} if status else {}

    def put_bucket_versioning(self, bucket: str, status: str) -> dict:
        self._logger.info("put_bucket_versioning bucket=%s status=%s", bucket, status)
        self._require_bucket(bucket)
        self._versioning[bucket] = status
        return {}

    # ── ACLs ──────────────────────────────────────────────────────────

    _DEFAULT_ACL = {
        "Owner": {"DisplayName": "admin", "ID": "admin"},
        "Grants": [
            {
                "Grantee": {
                    "DisplayName": "admin",
                    "ID": "admin",
                    "Type": "CanonicalUser",
                },
                "Permission": "FULL_CONTROL",
            }
        ],
    }

    def get_bucket_acl(self, bucket: str) -> dict:
        self._logger.info("get_bucket_acl bucket=%s", bucket)
        self._require_bucket(bucket)
        return self._bucket_acls.get(bucket, self._DEFAULT_ACL.copy())

    def put_bucket_acl(self, bucket: str, acl: dict) -> dict:
        self._logger.info("put_bucket_acl bucket=%s", bucket)
        self._require_bucket(bucket)
        self._bucket_acls[bucket] = acl
        return {}

    def get_object_acl(self, bucket: str, key: str) -> dict:
        self._logger.info("get_object_acl bucket=%s key=%s", bucket, key)
        self._require_object(bucket, key)
        return self._object_acls.get((bucket, key), self._DEFAULT_ACL.copy())

    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict:
        self._logger.info("put_object_acl bucket=%s key=%s", bucket, key)
        self._require_object(bucket, key)
        self._object_acls[(bucket, key)] = acl
        return {}


# ── Seed data ────────────────────────────────────────────────────────


def seed_s3(s3: MockS3Service) -> None:
    """Pre-populate the mock S3 with sample buckets and objects."""
    now = datetime.now(timezone.utc).isoformat()

    for name in ("documents", "archives", "logs"):
        s3._buckets[name] = {"CreationDate": now}
        s3._objects[name] = {}

    # Sample objects
    s3._objects["documents"]["readme.txt"] = _StoredObject(
        b"Welcome to the HCP mock server.\nThis is sample data for development.",
        "text/plain",
    )
    s3._objects["documents"]["reports/q1.csv"] = _StoredObject(
        b"month,revenue\nJan,1000\nFeb,1200\nMar,1500\n",
        "text/csv",
    )
    s3._objects["documents"]["reports/q2.csv"] = _StoredObject(
        b"month,revenue\nApr,1100\nMay,1300\nJun,1600\n",
        "text/csv",
    )
    s3._objects["archives"]["2024-backup.tar.gz"] = _StoredObject(
        b"\x1f\x8b" + b"\x00" * 50,  # fake gzip header
        "application/gzip",
    )
    s3._objects["logs"]["app.log"] = _StoredObject(
        b"2024-01-01 INFO  Server started\n2024-01-01 INFO  Ready\n",
        "text/plain",
    )
