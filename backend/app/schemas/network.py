"""Network settings models."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional
from .common import DownstreamDNSMode


class NetworkSettings(BaseModel):
    downstreamDNSMode: Optional[DownstreamDNSMode] = None
