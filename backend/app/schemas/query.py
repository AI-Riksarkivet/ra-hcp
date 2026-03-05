"""Pydantic models for the HCP Metadata Query API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request models ────────────────────────────────────────────────────


class ObjectQuery(BaseModel):
    """Parameters for an object-based metadata query."""

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(description="Query expression (Lucene syntax)")
    count: int = Field(default=100, description="Max results to return", alias="count")
    offset: int = Field(default=0, description="Starting offset")
    sort: Optional[str] = Field(
        default=None,
        description="Sort field (+/- prefix for asc/desc)",
        alias="sort",
    )
    verbose: bool = Field(default=False, description="Include full metadata")
    object_properties: Optional[list[str]] = Field(
        default=None,
        alias="objectProperties",
        description="Specific properties to return",
    )
    facets: Optional[list[str]] = Field(
        default=None, description="Facet fields to aggregate"
    )


class OperationSystemMetadataTransactions(BaseModel):
    """Transaction type filter for operation queries."""

    model_config = ConfigDict(populate_by_name=True)

    transaction: Optional[list[str]] = Field(
        default=None, description="Transaction types: create, delete, purge, dispose"
    )


class ChangeTimeRange(BaseModel):
    """Time range filter for operation queries."""

    model_config = ConfigDict(populate_by_name=True)

    start: Optional[str] = Field(
        default=None, description="Start time (epoch ms or ISO 8601)"
    )
    end: Optional[str] = Field(
        default=None, description="End time (epoch ms or ISO 8601)"
    )


class NamespaceList(BaseModel):
    """Namespace filter wrapper for operation queries."""

    model_config = ConfigDict(populate_by_name=True)

    namespace: Optional[list[str]] = Field(
        default=None, description="List of namespace names"
    )


class OperationSystemMetadata(BaseModel):
    """System metadata filter for operation queries."""

    model_config = ConfigDict(populate_by_name=True)

    change_time: Optional[ChangeTimeRange] = Field(
        default=None,
        alias="changeTime",
        description="Time range filter",
    )
    namespaces: Optional[NamespaceList] = Field(
        default=None, description="Filter to specific namespaces"
    )
    transactions: Optional[OperationSystemMetadataTransactions] = Field(
        default=None, description="Transaction type filters"
    )


class OperationQuery(BaseModel):
    """Parameters for an operation-based metadata query."""

    model_config = ConfigDict(populate_by_name=True)

    count: int = Field(default=100, description="Max results to return")
    verbose: bool = Field(default=False, description="Include full metadata")
    system_metadata: Optional[OperationSystemMetadata] = Field(
        default=None,
        alias="systemMetadata",
        description="System metadata filters",
    )


class ObjectQueryRequest(BaseModel):
    """Wire format: ``{"object": {...}}``."""

    model_config = ConfigDict(populate_by_name=True)

    object: ObjectQuery = Field(alias="object")


class OperationQueryRequest(BaseModel):
    """Wire format: ``{"operation": {...}}``."""

    model_config = ConfigDict(populate_by_name=True)

    operation: OperationQuery = Field(alias="operation")


# ── Response models ───────────────────────────────────────────────────


class QueryResultObject(BaseModel):
    """A single result entry from an object or operation query."""

    model_config = ConfigDict(populate_by_name=True)

    url_name: str = Field(alias="urlName")
    operation: str = Field(default="")
    change_time_milliseconds: Optional[str] = Field(
        default=None, alias="changeTimeMilliseconds"
    )
    change_time_string: Optional[str] = Field(default=None, alias="changeTimeString")
    version: Optional[str] = Field(default=None)
    namespace: Optional[str] = Field(default=None)
    utf8_name: Optional[str] = Field(default=None, alias="utf8Name")
    size: Optional[int] = Field(default=None)
    content_type: Optional[str] = Field(default=None, alias="contentType")
    hold: Optional[bool] = Field(default=None)
    retention: Optional[str] = Field(default=None)
    retention_string: Optional[str] = Field(default=None, alias="retentionString")
    retention_class: Optional[str] = Field(default=None, alias="retentionClass")
    hash_value: Optional[str] = Field(default=None, alias="hash")
    custom_metadata: Optional[bool] = Field(default=None, alias="customMetadata")
    replicated: Optional[bool] = Field(default=None)
    index: Optional[bool] = Field(default=None)
    ingest_time_milliseconds: Optional[str] = Field(
        default=None, alias="ingestTimeMilliseconds"
    )
    owner: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)


class QueryStatus(BaseModel):
    """Status block returned with every query response."""

    model_config = ConfigDict(populate_by_name=True)

    total_results: int = Field(alias="totalResults", default=0)
    results: int = Field(default=0)
    code: str = Field(default="COMPLETE")
    message: Optional[str] = Field(default=None)


class FacetFrequency(BaseModel):
    """A single facet value + count."""

    model_config = ConfigDict(populate_by_name=True)

    value: str
    count: int


class Facet(BaseModel):
    """A facet field with its frequency list."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    frequency: list[FacetFrequency] = Field(default_factory=list)


class ObjectQueryResponse(BaseModel):
    """Response from an object metadata query."""

    model_config = ConfigDict(populate_by_name=True)

    status: QueryStatus
    resultSet: list[QueryResultObject] = Field(default_factory=list, alias="resultSet")
    facets: Optional[list[Facet]] = Field(default=None)


class OperationQueryResponse(BaseModel):
    """Response from an operation metadata query."""

    model_config = ConfigDict(populate_by_name=True)

    status: QueryStatus
    resultSet: list[QueryResultObject] = Field(default_factory=list, alias="resultSet")
