"""Serialize arbitrary PyArrow values into JSON-safe Python objects.

Handles: binary (size-only), temporal, struct, map, list,
float NaN/Inf filtering, and all scalar types.
No content inspection on binary data — the /cell endpoint serves raw bytes.
"""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from typing import Any


def _clean_float(v: float) -> float | None:
    """Replace NaN / Inf with None for JSON compatibility."""
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def serialize_value(value: Any) -> Any:
    """Convert a single PyArrow-deserialized value into a JSON-safe object.

    Called per-cell after `to_pylist()`. Handles:
    - None → None
    - bytes → {"size": N}  (content served via /cell endpoint)
    - date/datetime/time/timedelta → ISO string
    - dict (struct/map) → recursively serialize values
    - list → recursively serialize items, clean NaN/Inf in float lists
    - float → NaN/Inf → None
    - everything else → pass through
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        return {"size": len(value)}

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, time):
        return value.isoformat()

    if isinstance(value, timedelta):
        return str(value)

    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}

    if isinstance(value, list):
        if value and all(isinstance(x, (int, float)) for x in value):
            return [_clean_float(float(x)) for x in value]
        return [serialize_value(item) for item in value]

    if isinstance(value, float):
        return _clean_float(value)

    return value
