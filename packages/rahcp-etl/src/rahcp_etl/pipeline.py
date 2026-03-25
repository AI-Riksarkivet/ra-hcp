"""Pipeline DAG — stage registration, retry policy, checkpoint resume."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from rahcp_etl.checkpointing import CheckpointStore

log = logging.getLogger(__name__)


@dataclass
class Stage:
    """A single pipeline stage with retry configuration."""

    name: str
    handler: Callable[..., Coroutine[Any, Any, dict[str, Any]]]
    retries: int = 3
    backoff: float = 2.0


class Pipeline:
    """Composable ETL pipeline with retry policy per stage.

    Register stages with the ``@pipeline.stage()`` decorator, then run
    with ``pipeline.run(payload)``. Each stage receives the output of
    the previous stage. Checkpoints are saved after each successful stage
    so the pipeline can resume on failure.

    Example::

        pipeline = Pipeline()

        @pipeline.stage("extract", retries=3)
        async def extract(payload):
            ...
            return {"records": [...]}

        @pipeline.stage("transform")
        async def transform(payload):
            ...
            return {"transformed": [...]}

        result = await pipeline.run({"source": "s3://..."})
    """

    def __init__(self, checkpoint_store: CheckpointStore | None = None) -> None:
        self._stages: list[Stage] = []
        self._checkpoint_store = checkpoint_store

    def stage(
        self,
        name: str,
        *,
        retries: int = 3,
        backoff: float = 2.0,
    ) -> Callable:
        """Decorator to register a pipeline stage."""

        def decorator(
            fn: Callable[..., Coroutine[Any, Any, dict[str, Any]]],
        ) -> Callable[..., Coroutine[Any, Any, dict[str, Any]]]:
            self._stages.append(
                Stage(name=name, handler=fn, retries=retries, backoff=backoff)
            )
            return fn

        return decorator

    async def run(
        self,
        payload: dict[str, Any],
        *,
        pipeline_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute all stages in order with retry and checkpointing."""
        state = dict(payload)
        start_index = 0

        # Resume from checkpoint if available
        if pipeline_id and self._checkpoint_store:
            checkpoint = await self._checkpoint_store.load(pipeline_id)
            if checkpoint:
                completed_stage = checkpoint["stage"]
                state = checkpoint["state"]
                for i, s in enumerate(self._stages):
                    if s.name == completed_stage:
                        start_index = i + 1
                        break
                log.info(
                    "Resuming pipeline %s from stage %d (%s)",
                    pipeline_id,
                    start_index,
                    completed_stage,
                )

        for stage in self._stages[start_index:]:
            state = await self._run_stage(stage, state)
            if pipeline_id and self._checkpoint_store:
                await self._checkpoint_store.save(pipeline_id, stage.name, state)

        # Clear checkpoint on success
        if pipeline_id and self._checkpoint_store:
            await self._checkpoint_store.clear(pipeline_id)

        return state

    async def _run_stage(self, stage: Stage, state: dict[str, Any]) -> dict[str, Any]:
        """Run a single stage with retry."""
        last_error: Exception | None = None
        for attempt in range(stage.retries + 1):
            try:
                result = await stage.handler(state)
                log.info("Stage '%s' completed", stage.name)
                return result
            except Exception as exc:
                last_error = exc
                if attempt < stage.retries:
                    delay = stage.backoff * (2**attempt)
                    log.warning(
                        "Stage '%s' failed (attempt %d/%d), retrying in %.1fs: %s",
                        stage.name,
                        attempt + 1,
                        stage.retries + 1,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)

        log.error("Stage '%s' failed after %d attempts", stage.name, stage.retries + 1)
        raise last_error  # type: ignore[misc]
