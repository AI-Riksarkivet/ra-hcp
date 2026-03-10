"""Lance service for browsing and managing .lance datasets on HCP S3.

Uses lancedb (database library) for table management and the underlying
lance.LanceDataset for native push-down reads (projection, filter,
limit/offset, take). All I/O is pushed to the S3 storage layer.
"""

from __future__ import annotations

import logging
from typing import Any

import lancedb
import pyarrow as pa
from opentelemetry import trace

from app.services.serialize_value import _clean_float, serialize_value

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

_MAX_PREVIEW = 32


class LanceError(Exception):
    """Raised when a Lance dataset cannot be read (corrupt, missing, etc.)."""


def _is_vector_field(field: pa.Field) -> bool:
    return (
        pa.types.is_list(field.type) and pa.types.is_floating(field.type.value_type)
    ) or (
        pa.types.is_fixed_size_list(field.type)
        and pa.types.is_floating(field.type.value_type)
    )


def _is_binary_field(field: pa.Field) -> bool:
    return pa.types.is_binary(field.type) or pa.types.is_large_binary(field.type)


def _serialize_vector(vec: list[float]) -> dict:
    """Serialize a vector column value to a dict with stats + preview."""
    clean = [_clean_float(x) for x in vec]
    valid_floats = [x for x in clean if x is not None]
    if not valid_floats:
        return {
            "type": "vector",
            "dim": len(vec),
            "norm": 0,
            "min": 0,
            "max": 0,
            "mean": 0,
            "preview": clean[:_MAX_PREVIEW],
        }
    norm = sum(x * x for x in valid_floats) ** 0.5
    return {
        "type": "vector",
        "dim": len(vec),
        "norm": _clean_float(norm),
        "min": min(valid_floats),
        "max": max(valid_floats),
        "mean": sum(valid_floats) / len(valid_floats),
        "preview": clean[:_MAX_PREVIEW],
    }


class LanceService:
    """Lance database connection to an S3-hosted dataset directory.

    Uses lancedb for table management (list/open/create/delete) and
    accesses the underlying lance.LanceDataset for native push-down reads.

    All methods are synchronous — endpoints call via asyncio.to_thread().
    """

    def __init__(self, base_uri: str, storage_options: dict[str, str]):
        self._base_uri = base_uri
        self._storage_options = storage_options
        try:
            self._db = lancedb.connect(
                base_uri,
                storage_options=storage_options,
            )
        except Exception as exc:
            raise LanceError(f"Cannot connect to {base_uri}: {exc}") from exc

    @classmethod
    def with_credentials(
        cls,
        base_uri: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        *,
        verify_ssl: bool = True,
    ) -> LanceService:
        opts: dict[str, str] = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "allow_http": "false",
        }
        if not verify_ssl:
            opts["aws_allow_invalid_certificates"] = "true"
        return cls(base_uri, storage_options=opts)

    def _open_lance_dataset(self, table_name: str):
        """Open a table and return the underlying lance.LanceDataset."""
        try:
            table = self._db.open_table(table_name)
            return table.to_lance()
        except Exception as exc:
            raise LanceError(f"Cannot open table {table_name!r}: {exc}") from exc

    # ── Table management ──────────────────────────────────────────

    def list_tables(self) -> list[str]:
        """List all table names in the database.

        Uses db.list_tables() (lancedb >=0.29) which returns a paginated
        result with .tables (list[str]) and .page_token (str | None).
        """
        with tracer.start_as_current_span("lance.list_tables"):
            try:
                all_names: list[str] = []
                page_token: str | None = None
                while True:
                    result = self._db.list_tables(page_token=page_token, limit=100)
                    # list_tables() returns a dict-like with 'tables' and 'page_token'
                    names: list[str] = (
                        result.tables
                        if hasattr(result, "tables")
                        else result.get("tables", [])
                        if isinstance(result, dict)
                        else list(result)
                    )
                    if not names:
                        break
                    all_names.extend(names)
                    # Get next page token
                    next_token = (
                        result.page_token
                        if hasattr(result, "page_token")
                        else result.get("page_token")
                        if isinstance(result, dict)
                        else None
                    )
                    if not next_token or len(names) < 100:
                        break
                    page_token = next_token
                return all_names
            except Exception as exc:
                raise LanceError(
                    f"Cannot list tables at {self._base_uri}: {exc}"
                ) from exc

    def get_schema(self, table_name: str) -> dict[str, Any]:
        """Return schema fields with vector/binary column detection."""
        with tracer.start_as_current_span("lance.get_schema") as span:
            span.set_attribute("lance.table", table_name)
            ds = self._open_lance_dataset(table_name)
            fields = []
            for field in ds.schema:
                is_vector = _is_vector_field(field)
                is_binary = _is_binary_field(field)
                dim = None
                if is_vector and pa.types.is_fixed_size_list(field.type):
                    dim = field.type.list_size
                fields.append(
                    {
                        "name": field.name,
                        "type": str(field.type),
                        "nullable": field.nullable,
                        "is_vector": is_vector,
                        "is_binary": is_binary,
                        "vector_dim": dim,
                    }
                )
            return {"table_name": table_name, "fields": fields}

    # ── Data reads (all use native Lance push-down) ───────────────

    def get_rows(
        self,
        table_name: str,
        limit: int = 50,
        offset: int = 0,
        columns: list[str] | None = None,
        filter_expr: str | None = None,
    ) -> dict[str, Any]:
        """Return paginated rows using Lance's native push-down."""
        with tracer.start_as_current_span("lance.get_rows") as span:
            span.set_attribute("lance.table", table_name)
            span.set_attribute("lance.limit", limit)
            span.set_attribute("lance.offset", offset)

            ds = self._open_lance_dataset(table_name)

            try:
                total = ds.count_rows(filter=filter_expr)
            except Exception as exc:
                raise LanceError(f"Cannot count rows in {table_name!r}: {exc}") from exc

            try:
                arrow_table = ds.to_table(
                    columns=columns,
                    filter=filter_expr,
                    limit=limit,
                    offset=offset,
                )
            except Exception as exc:
                raise LanceError(f"Cannot read {table_name!r}: {exc}") from exc

            rows = arrow_table.to_pylist()

            vector_fields = {f.name for f in ds.schema if _is_vector_field(f)}

            for row in rows:
                for col, val in row.items():
                    if val is None:
                        continue
                    if col in vector_fields:
                        row[col] = _serialize_vector(val)
                    else:
                        row[col] = serialize_value(val)

            return {
                "rows": rows,
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    def get_vector_preview(
        self, table_name: str, column: str, limit: int = 100
    ) -> dict[str, Any]:
        """Return stats + sample vectors for a vector column."""
        with tracer.start_as_current_span("lance.vector_preview") as span:
            span.set_attribute("lance.table", table_name)
            span.set_attribute("lance.column", column)

            ds = self._open_lance_dataset(table_name)
            try:
                result = ds.to_table(columns=[column], limit=limit)
            except Exception as exc:
                raise LanceError(
                    f"Cannot read vector column {column!r}: {exc}"
                ) from exc

            vectors = result.column(0).to_pylist()
            valid = [v for v in vectors if v is not None]

            if not valid:
                return {"stats": None, "preview": []}

            all_vals = [_clean_float(x) for vec in valid for x in vec]
            clean_vals = [x for x in all_vals if x is not None]
            if not clean_vals:
                return {"stats": None, "preview": []}

            stats = {
                "count": len(valid),
                "dim": len(valid[0]),
                "min": min(clean_vals),
                "max": max(clean_vals),
                "mean": sum(clean_vals) / len(clean_vals),
            }

            preview = []
            for v in valid[:20]:
                cleaned = [_clean_float(x) for x in v]
                valid_f = [x for x in cleaned if x is not None]
                norm = sum(x * x for x in valid_f) ** 0.5 if valid_f else 0.0
                preview.append(
                    {
                        "norm": _clean_float(norm),
                        "sample": cleaned[:_MAX_PREVIEW],
                    }
                )
            return {"stats": stats, "preview": preview}

    def get_cell_bytes(self, table_name: str, column: str, row: int) -> bytes | None:
        """Return raw bytes for a single cell using Lance's take()."""
        with tracer.start_as_current_span("lance.get_cell_bytes") as span:
            span.set_attribute("lance.table", table_name)
            span.set_attribute("lance.column", column)
            span.set_attribute("lance.row", row)

            ds = self._open_lance_dataset(table_name)
            try:
                batch = ds.take([row], columns=[column])
            except Exception as exc:
                raise LanceError(f"Cannot read cell {column}[{row}]: {exc}") from exc

            if batch.num_rows == 0:
                return None

            value = batch.column(0)[0].as_py()
            if value is None:
                return None
            if isinstance(value, bytes):
                return value
            return str(value).encode()
