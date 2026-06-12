"""Dead-letter queue handler — route failed messages for inspection/replay."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import nats  # ty: ignore[unresolved-import]
from nats.js import JetStreamContext  # ty: ignore[unresolved-import]

log = logging.getLogger(__name__)

DLQ_STREAM = "etl-dlq"
DLQ_SUBJECT = "etl.dlq.>"


def _as_utc(value: datetime) -> datetime:
    """Normalize a message timestamp to an aware UTC datetime."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class DeadLetterHandler:
    """Route permanently-failed messages to a DLQ stream for inspection/replay.

    Messages in the DLQ include the original payload, the error message,
    and the original subject for targeted replay.
    """

    def __init__(self, js: JetStreamContext) -> None:
        self._js = js

    @classmethod
    async def create(cls, nc: nats.NATS) -> DeadLetterHandler:
        """Create the DLQ handler, ensuring the DLQ stream exists."""
        js = nc.jetstream()
        await js.find_stream_name_by_subject(DLQ_SUBJECT)
        return cls(js)

    async def send(
        self,
        subject: str,
        payload: bytes,
        error: str,
    ) -> None:
        """Send a failed message to the DLQ."""
        import json

        dlq_payload = json.dumps(
            {
                "original_subject": subject,
                "payload": payload.decode("utf-8", errors="replace"),
                "error": error,
            }
        ).encode()
        dlq_subject = f"etl.dlq.{subject}"
        await self._js.publish(dlq_subject, dlq_payload)
        log.warning("Message sent to DLQ: %s — %s", subject, error)

    async def replay(self, *, filter_subject: str | None = None) -> int:
        """Replay DLQ messages back to their original subjects.

        Returns the number of messages replayed.
        """
        import json

        sub_subject = f"etl.dlq.{filter_subject}" if filter_subject else DLQ_SUBJECT
        sub = await self._js.subscribe(
            sub_subject, stream=DLQ_STREAM, ordered_consumer=True
        )

        count = 0
        async for msg in sub.messages:
            try:
                data = json.loads(msg.data)
                original_subject = data["original_subject"]
                original_payload = data["payload"].encode()
                await self._js.publish(original_subject, original_payload)
                count += 1
            except Exception:
                log.exception("Failed to replay DLQ message")
            # Stop after draining existing messages
            if msg.pending == 0:
                break

        await sub.unsubscribe()
        log.info("Replayed %d DLQ messages", count)
        return count

    async def purge(self, *, older_than: timedelta | None = None) -> int:
        """Purge DLQ messages, optionally only those older than ``older_than``.

        Returns the number of messages purged.
        """
        info = await self._js.stream_info(DLQ_STREAM)
        before = info.state.messages
        if before == 0:
            return 0

        if older_than is None:
            await self._js.purge_stream(DLQ_STREAM)
            log.info("Purged %d DLQ messages", before)
            return before

        cutoff = datetime.now(UTC) - older_than
        first_keep = await self._first_seq_at_or_after(
            info.state.first_seq, info.state.last_seq, cutoff
        )
        if first_keep is None:
            await self._js.purge_stream(DLQ_STREAM)
            log.info("Purged %d DLQ messages (all older than %s)", before, older_than)
            return before
        if first_keep <= info.state.first_seq:
            return 0

        # JetStream purge with ``seq`` removes messages below that sequence.
        await self._js.purge_stream(DLQ_STREAM, seq=first_keep)
        after = (await self._js.stream_info(DLQ_STREAM)).state.messages
        purged = before - after
        log.info("Purged %d DLQ messages older than %s", purged, older_than)
        return purged

    async def _first_seq_at_or_after(
        self, lo: int, hi: int, cutoff: datetime
    ) -> int | None:
        """Binary-search the lowest sequence whose message time is >= ``cutoff``.

        Returns ``None`` when even the newest message is older than the cutoff.
        Message timestamps are monotonic in sequence, so bisection is safe; the
        ``next_by_subj`` lookup tolerates gaps from previously deleted messages.
        """
        if await self._msg_time(hi) < cutoff:
            return None
        while lo < hi:
            mid = (lo + hi) // 2
            if await self._msg_time(mid) < cutoff:
                lo = mid + 1
            else:
                hi = mid
        return lo

    async def _msg_time(self, seq: int) -> datetime:
        """Timestamp of the first DLQ message at or after ``seq``."""
        msg = await self._js.get_msg(
            DLQ_STREAM, seq=seq, subject=DLQ_SUBJECT, next=True
        )
        return _as_utc(msg.time)
