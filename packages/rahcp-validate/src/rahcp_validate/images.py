"""Image integrity checks — TIFF and JPEG corruption detection."""

from __future__ import annotations

from pathlib import Path

from PIL import Image  # ty: ignore[unresolved-import]


class ValidationError(Exception):
    """Raised when a file fails validation."""

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"{path}: {reason}")
        self.path = path
        self.reason = reason


def validate_tiff(path: Path) -> None:
    """Verify a TIFF file is not corrupt and meets basic requirements.

    Checks magic bytes, IFD structure, and that Pillow can fully load it.
    Raises ``ValidationError`` on failure.
    """
    _check_exists(path)

    # Check magic bytes (II for little-endian, MM for big-endian)
    with path.open("rb") as f:
        header = f.read(4)
    if len(header) < 4:
        raise ValidationError(path, "File too small to be a valid TIFF")
    if header[:2] not in (b"II", b"MM"):
        raise ValidationError(path, f"Invalid TIFF byte order marker: {header[:2]!r}")
    version = int.from_bytes(header[2:4], "little" if header[:2] == b"II" else "big")
    if version != 42:
        raise ValidationError(path, f"Invalid TIFF version: {version} (expected 42)")

    # Full load to detect truncation/corruption
    try:
        with Image.open(path) as img:
            img.load()
    except Exception as exc:
        raise ValidationError(path, f"TIFF load failed: {exc}") from exc


def validate_jpg(path: Path) -> None:
    """Verify a JPEG file is not corrupt.

    Checks SOI/EOI markers and that Pillow can fully load it.
    Raises ``ValidationError`` on failure.
    """
    _check_exists(path)

    with path.open("rb") as f:
        header = f.read(2)
        if header != b"\xff\xd8":
            raise ValidationError(path, "Missing JPEG SOI marker")
        # Seek to end to check EOI
        f.seek(-2, 2)
        trailer = f.read(2)
    if trailer != b"\xff\xd9":
        raise ValidationError(path, "Missing JPEG EOI marker (possibly truncated)")

    try:
        with Image.open(path) as img:
            img.load()
    except Exception as exc:
        raise ValidationError(path, f"JPEG load failed: {exc}") from exc


def _check_exists(path: Path) -> None:
    if not path.exists():
        raise ValidationError(path, "File does not exist")
    if not path.is_file():
        raise ValidationError(path, "Path is not a file")
