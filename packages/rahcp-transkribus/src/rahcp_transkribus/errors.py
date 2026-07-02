"""Exception hierarchy for Transkribus operations."""

from __future__ import annotations


class TranskribusError(Exception):
    """Base error for all Transkribus operations."""


class TranskribusAuthError(TranskribusError):
    """Login failed or the session was rejected."""
