"""OpenTelemetry setup — traces, metrics, and structured logging."""

from __future__ import annotations

import json as _json
import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)


# ── JSON log formatter ────────────────────────────────────────────────

_EXTRA_FIELDS = (
    "request_id",
    "method",
    "path",
    "query",
    "status",
    "duration_ms",
    "user",
    "client_ip",
    "trace_id",
    "span_id",
)


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in _EXTRA_FIELDS:
            val = getattr(record, key, None)
            if val is not None:
                entry[key] = val
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return _json.dumps(entry, default=str)


_resource = Resource.create({"service.name": "hcp-api"})


def setup_telemetry(app: FastAPI) -> None:
    """Initialise OTel providers, exporters, and auto-instrumentation."""

    # ── Trace provider ────────────────────────────────────────────────
    tracer_provider = TracerProvider(resource=_resource)

    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    else:
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(tracer_provider)

    # ── Metrics provider ──────────────────────────────────────────────
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

        reader = PeriodicExportingMetricReader(OTLPMetricExporter())
        meter_provider = MeterProvider(resource=_resource, metric_readers=[reader])
    else:
        # No periodic console metric exporter — it spawns a background thread
        # that can error on process shutdown (e.g. during tests).
        meter_provider = MeterProvider(resource=_resource)

    metrics.set_meter_provider(meter_provider)

    # ── Auto-instrumentation ──────────────────────────────────────────
    def _server_request_hook(span, scope):
        """Redact Authorization header from inbound request spans."""
        if span.is_recording():
            span.set_attribute("http.request.header.authorization", "[REDACTED]")

    def _client_request_hook(span, request):
        """Redact Authorization header from outbound HTTPX request spans."""
        if span.is_recording():
            span.set_attribute("http.request.header.authorization", "[REDACTED]")

    FastAPIInstrumentor.instrument_app(app, server_request_hook=_server_request_hook)
    HTTPXClientInstrumentor().instrument(request_hook=_client_request_hook)

    # ── Structured JSON logging ────────────────────────────────────────
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    logging.root.handlers.clear()
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
    logging.getLogger(__name__).info("Telemetry initialised (service.name=hcp-api)")
