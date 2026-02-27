#!/usr/bin/env bash
# Download large object from HCP S3 and verify size
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

LARGE_SIZE=$(stat --format=%s /tmp/hcp-test-large.bin 2>/dev/null || stat -f%z /tmp/hcp-test-large.bin 2>/dev/null)

echo "Downloading large object..."
SECONDS=0
if aws s3api get-object $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" \
    --key "test-large.bin" \
    /tmp/hcp-test-large-dl.bin 2>&1; then
    DL_SIZE=$(stat --format=%s /tmp/hcp-test-large-dl.bin 2>/dev/null || stat -f%z /tmp/hcp-test-large-dl.bin 2>/dev/null)
    if [ "$LARGE_SIZE" = "$DL_SIZE" ]; then
        ok "Download OK — size matches (${DL_SIZE} bytes) in ${SECONDS}s"
    else
        fail "Size mismatch! Upload: ${LARGE_SIZE}, Download: ${DL_SIZE}"
    fi
else
    fail "Download failed"
fi
