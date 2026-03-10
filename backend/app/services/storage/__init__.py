"""Backend-agnostic storage abstraction layer."""

from app.services.storage.base import StorageBase
from app.services.storage.errors import (
    StorageError,
    StorageOperationNotSupported,
    StorageTransportError,
)
from app.services.storage.protocol import StorageProtocol

__all__ = [
    "StorageBase",
    "StorageError",
    "StorageOperationNotSupported",
    "StorageProtocol",
    "StorageTransportError",
]
