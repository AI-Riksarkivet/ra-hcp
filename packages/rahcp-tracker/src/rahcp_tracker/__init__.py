"""rahcp-tracker — pluggable transfer state tracking.

::

    from rahcp_tracker import TrackerProtocol, TransferStatus, create_tracker
"""

from rahcp_tracker.factory import create_tracker, redact_dsn
from rahcp_tracker.models import Transfer, TransferStatus
from rahcp_tracker.postgres import PostgresTracker
from rahcp_tracker.protocol import TrackerProtocol
from rahcp_tracker.sqlite import SqliteTracker

# Backwards-compatible alias
TransferTracker = SqliteTracker

__all__ = [
    "PostgresTracker",
    "TrackerProtocol",
    "Transfer",
    "TransferStatus",
    "SqliteTracker",
    "TransferTracker",
    "create_tracker",
    "redact_dsn",
]
