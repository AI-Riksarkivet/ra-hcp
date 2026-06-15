"""A minimal fake IIIF Image API server for end-to-end tests.

Serves just enough of the Riksarkivet IIIF surface that ``rahcp iiif upload``
exercises:

* ``GET /arkis!{batch}/manifest`` → a Presentation-API manifest whose ``items``
  carry ``arkis!{image_id}/canvas`` ids (the SDK extracts the 14-char id after
  the ``!``).
* ``GET /arkis!{image_id}/{region}/{size}/{rotation}/{quality}.{fmt}`` → a real,
  Pillow-encoded JPEG so the ``--validate`` byte check decodes actual image data.

Config via env vars:
    IIIF_BATCH        batch id (default ``A0099999`` — 8 chars so image ids hit 14)
    IIIF_NUM_IMAGES   images in the manifest (default ``5``)
    IIIF_PORT         listen port (default ``80``)

Run: ``python fake_iiif_server.py``
"""

from __future__ import annotations

import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image

BATCH = os.environ.get("IIIF_BATCH", "A0099999")
NUM_IMAGES = int(os.environ.get("IIIF_NUM_IMAGES", "5"))
PORT = int(os.environ.get("IIIF_PORT", "80"))


def image_ids() -> list[str]:
    """Image ids for the batch, e.g. ``A0099999_00001`` (14 chars total)."""
    return [f"{BATCH}_{n:05d}" for n in range(1, NUM_IMAGES + 1)]


def manifest() -> dict[str, object]:
    """A minimal IIIF Presentation manifest the SDK can parse."""
    return {
        "@context": "http://iiif.io/api/presentation/3/context.json",
        "id": f"/arkis!{BATCH}/manifest",
        "type": "Manifest",
        "items": [
            {"id": f"https://example/arkis!{img}/canvas", "type": "Canvas"}
            for img in image_ids()
        ],
    }


def jpeg_bytes(seed: int) -> bytes:
    """A small but genuinely valid JPEG, varied per image so sizes differ."""
    color = (seed * 37 % 256, seed * 53 % 256, seed * 97 % 256)
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, format="JPEG")
    return buf.getvalue()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 — base API name
        pass

    def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler API
        path = self.path
        if path == f"/arkis!{BATCH}/manifest":
            self._send(200, "application/json", json.dumps(manifest()).encode())
            return
        if path.startswith("/arkis!") and path.endswith(".jpg"):
            raw_id = path.removeprefix("/arkis!").split("/", 1)[0]
            ids = image_ids()
            if raw_id in ids:
                self._send(200, "image/jpeg", jpeg_bytes(ids.index(raw_id) + 1))
                return
        self._send(404, "text/plain", b"not found")

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"fake-iiif serving batch {BATCH} ({NUM_IMAGES} images) on :{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
