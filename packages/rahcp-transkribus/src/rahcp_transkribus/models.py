"""Pydantic models for the Transkribus REST API and export planning."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Transcript(BaseModel):
    """One transcript version attached to a page (newest matching first)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    file_name: str | None = Field(default=None, alias="fileName")
    url: str | None = None
    status: str | None = None
    ts_id: int | None = Field(default=None, alias="tsId")


class TsList(BaseModel):
    """Wrapper around a page's transcript versions."""

    model_config = ConfigDict(extra="ignore")

    transcripts: list[Transcript] = Field(default_factory=list)


class Page(BaseModel):
    """A single page in a Transkribus document."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    page_nr: int = Field(alias="pageNr")
    url: str | None = None
    img_file_name: str | None = Field(default=None, alias="imgFileName")
    ts_list: TsList = Field(default_factory=TsList, alias="tsList")


class Document(BaseModel):
    """Document metadata as returned by the collection listing."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    doc_id: int = Field(alias="docId")
    title: str = ""
    nr_of_pages: int | None = Field(default=None, alias="nrOfPages")


class ItemKind(StrEnum):
    """What an export item holds — a page transcript or its page image."""

    transcript = "transcript"
    image = "image"


class ExportItem(BaseModel):
    """One planned export unit: a destination key and where to fetch its bytes.

    ``key`` is a relative object key (no bucket prefix) usable both as a local
    path under an output directory and as an S3 key. ``url`` is the source URL
    to GET. When ``convert_alto`` is set, the fetched PAGE-XML is converted to
    ALTO before being written/uploaded.
    """

    key: str
    url: str
    kind: ItemKind
    doc_id: int
    page_nr: int
    convert_alto: bool = False
    ts_id: int | None = None
    """Transkribus transcript version id — set for transcripts, drives change detection."""


class ExportStats(BaseModel):
    """Counters for a local Transkribus export."""

    ok: int = 0
    skipped: int = 0
    errors: int = 0
    total_bytes: int = 0
    elapsed: float = 0.0

    @property
    def done(self) -> int:
        """Total items processed (ok + skipped + errors)."""
        return self.ok + self.skipped + self.errors

    @property
    def mb_per_sec(self) -> float:
        """Throughput in megabytes per second."""
        return (
            (self.total_bytes / 1024 / 1024) / self.elapsed if self.elapsed > 0 else 0.0
        )
