# rahcp-validate

Pre-upload file validation with format-specific checks and composable rules.

## Image validation

```python
from pathlib import Path
from rahcp_validate import validate_tiff, validate_jpg, validate_png, ValidationError

try:
    validate_tiff(Path("scan.tiff"))
    print("TIFF is valid")
except ValidationError as e:
    print(f"Invalid: {e.reason}")

try:
    validate_jpg(Path("photo.jpg"))
except ValidationError as e:
    print(f"Invalid: {e.reason}")
```

Or use `validate_by_extension()` to auto-detect format from the file extension:

```python
from rahcp_validate import validate_by_extension

# Automatically picks validate_jpg, validate_tiff, or validate_png based on extension
validate_by_extension(Path("scan.tiff"))  # runs TIFF checks
validate_by_extension(Path("photo.jpg"))  # runs JPEG checks
validate_by_extension(Path("image.png"))  # runs PNG checks
validate_by_extension(Path("data.csv"))   # skipped (no validator for .csv)
```

This is what the `--validate` flag on the disk commands (`iiif download`, `s3 upload-all`) uses internally.

### Validating in-memory bytes (streaming)

For streaming workflows that never touch disk (e.g. `rahcp iiif upload` /
`bulk_stream_upload`), validate the **bytes** directly — same magic-byte + full
Pillow decode checks, no file needed:

```python
from rahcp_validate import (
    validate_jpg_bytes, validate_png_bytes, validate_tiff_bytes,
    validate_bytes_by_extension, ValidationError,
)

data: bytes = ...  # e.g. an image just downloaded from IIIF

try:
    validate_jpg_bytes(data)                       # explicit format
    validate_bytes_by_extension(data, ".jpg")      # or dispatch by extension
except ValidationError as e:
    print(f"corrupt image: {e.reason}")
```

`validate_bytes_by_extension(data, ext)` is the callback the `iiif upload
--validate` flag passes to the streaming engine; the `Path` validators above
simply read the file and delegate to these, so disk and streaming share one
implementation.

**TIFF checks:** magic bytes (II/MM), version == 42, full Pillow load.

**JPEG checks:** SOI marker (0xFFD8), EOI marker (0xFFD9), full Pillow decode.

**PNG checks:** PNG signature bytes, full Pillow decode.

## Composable rules

```python
from pathlib import Path
from rahcp_validate.rules import validate, max_file_size, image_dimensions, allowed_extensions

rules = [
    max_file_size(100 * 1024 * 1024),         # 100 MB max
    allowed_extensions(".tiff", ".tif", ".jpg", ".jpeg"),
    image_dimensions(min_w=100, min_h=100, max_w=10000, max_h=10000),
]

errors = validate(Path("scan.tiff"), rules)
if errors:
    for e in errors:
        print(f"  FAIL: {e}")
else:
    print("All checks passed")
```

| Rule factory | Description |
|-------------|-------------|
| `max_file_size(limit_bytes)` | Reject files larger than limit |
| `image_dimensions(min_w, min_h, max_w, max_h)` | Check pixel dimensions are within bounds |
| `allowed_extensions(*exts)` | Only allow specified file extensions |
