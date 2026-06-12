"""Tests for the dead-letter queue handler — purge semantics."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from rahcp_etl.dlq import DLQ_STREAM, DLQ_SUBJECT, DeadLetterHandler

pytestmark = pytest.mark.asyncio

NOW = datetime.now(UTC)


def _stream_info(messages: int, first_seq: int = 1, last_seq: int = 0):
    return SimpleNamespace(
        state=SimpleNamespace(messages=messages, first_seq=first_seq, last_seq=last_seq)
    )


def _make_js(msg_times: dict[int, datetime], total: int | None = None):
    """Mock JetStream with messages at seqs of ``msg_times`` (monotonic times)."""
    seqs = sorted(msg_times)
    js = MagicMock()
    before = total if total is not None else len(seqs)
    infos = [_stream_info(before, first_seq=seqs[0], last_seq=seqs[-1])]
    js.stream_info = AsyncMock(side_effect=lambda _s: infos.pop(0))
    js.purge_stream = AsyncMock(return_value=True)

    async def get_msg(stream, seq=0, subject=None, next=False):
        assert stream == DLQ_STREAM and subject == DLQ_SUBJECT and next
        for s in seqs:
            if s >= seq:
                return SimpleNamespace(seq=s, time=msg_times[s])
        raise LookupError(f"no message at or after seq {seq}")

    js.get_msg = AsyncMock(side_effect=get_msg)
    return js, infos


async def test_purge_without_age_purges_everything():
    js = MagicMock()
    js.stream_info = AsyncMock(return_value=_stream_info(5, 1, 5))
    js.purge_stream = AsyncMock(return_value=True)

    purged = await DeadLetterHandler(js).purge()

    assert purged == 5
    js.purge_stream.assert_awaited_once_with(DLQ_STREAM)


async def test_purge_empty_stream_is_a_noop():
    js = MagicMock()
    js.stream_info = AsyncMock(return_value=_stream_info(0))
    js.purge_stream = AsyncMock()

    purged = await DeadLetterHandler(js).purge(older_than=timedelta(days=7))

    assert purged == 0
    js.purge_stream.assert_not_awaited()


async def test_purge_older_than_removes_only_old_messages():
    # seqs 1-3 are old (8 days), seqs 4-5 are fresh (1 hour)
    times = {
        1: NOW - timedelta(days=8),
        2: NOW - timedelta(days=8),
        3: NOW - timedelta(days=8),
        4: NOW - timedelta(hours=1),
        5: NOW - timedelta(minutes=5),
    }
    js, infos = _make_js(times)
    infos.append(_stream_info(2, first_seq=4, last_seq=5))  # state after purge

    purged = await DeadLetterHandler(js).purge(older_than=timedelta(days=7))

    assert purged == 3
    js.purge_stream.assert_awaited_once_with(DLQ_STREAM, seq=4)


async def test_purge_older_than_purges_all_when_everything_is_old():
    times = {1: NOW - timedelta(days=30), 2: NOW - timedelta(days=20)}
    js, _ = _make_js(times)

    purged = await DeadLetterHandler(js).purge(older_than=timedelta(days=7))

    assert purged == 2
    js.purge_stream.assert_awaited_once_with(DLQ_STREAM)


async def test_purge_older_than_keeps_everything_when_nothing_is_old():
    times = {1: NOW - timedelta(hours=2), 2: NOW - timedelta(minutes=1)}
    js, _ = _make_js(times)

    purged = await DeadLetterHandler(js).purge(older_than=timedelta(days=7))

    assert purged == 0
    js.purge_stream.assert_not_awaited()


async def test_purge_older_than_tolerates_sequence_gaps():
    # seq 2 was deleted; next_by_subj resolves a mid-search probe at seq 2
    # to the message at seq 3.
    times = {
        1: NOW - timedelta(days=10),
        3: NOW - timedelta(days=9),
        4: NOW - timedelta(hours=1),
    }
    js, infos = _make_js(times, total=3)
    infos.append(_stream_info(1, first_seq=4, last_seq=4))

    purged = await DeadLetterHandler(js).purge(older_than=timedelta(days=7))

    assert purged == 2
    js.purge_stream.assert_awaited_once_with(DLQ_STREAM, seq=4)


async def test_purge_naive_timestamps_are_treated_as_utc():
    naive_old = (NOW - timedelta(days=8)).replace(tzinfo=None)
    naive_new = (NOW - timedelta(hours=1)).replace(tzinfo=None)
    js, infos = _make_js({1: naive_old, 2: naive_new})
    infos.append(_stream_info(1, first_seq=2, last_seq=2))

    purged = await DeadLetterHandler(js).purge(older_than=timedelta(days=7))

    assert purged == 1
    js.purge_stream.assert_awaited_once_with(DLQ_STREAM, seq=2)
