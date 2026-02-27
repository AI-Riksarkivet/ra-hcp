#!/usr/bin/env bash
# Multipart upload: generate large file, split, upload parts, complete
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Generating ${MULTIPART_FILE_SIZE_MB}MB test file for multipart upload..."
dd if=/dev/urandom of=/tmp/hcp-test-large.bin \
    bs=1M count=${MULTIPART_FILE_SIZE_MB} 2>&1 | tail -1
LARGE_SIZE=$(stat --format=%s /tmp/hcp-test-large.bin 2>/dev/null || stat -f%z /tmp/hcp-test-large.bin 2>/dev/null)
echo "  File size: ${LARGE_SIZE} bytes ($(( LARGE_SIZE / 1024 / 1024 )) MB)"

echo "Multipart upload of ${MULTIPART_FILE_SIZE_MB}MB file..."
SECONDS=0

# Initiate multipart upload
echo "  Initiating multipart upload..."
UPLOAD_ID=$(aws s3api create-multipart-upload $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" \
    --key "test-large.bin" \
    --query 'UploadId' --output text 2>/dev/null)
echo "  UploadId: ${UPLOAD_ID}"

# Split file and upload parts
NUM_PARTS=$(( (LARGE_SIZE + CHUNK_SIZE_BYTES - 1) / CHUNK_SIZE_BYTES ))
PARTS_JSON="["
UPLOAD_OK=true

for (( i=1; i<=NUM_PARTS; i++ )); do
    SKIP=$(( (i - 1) * CHUNK_SIZE_MB ))
    REMAINING=$(( LARGE_SIZE - SKIP * 1024 * 1024 ))
    if [ "$REMAINING" -gt "$CHUNK_SIZE_BYTES" ]; then
        COUNT=$CHUNK_SIZE_MB
    else
        COUNT=$(( (REMAINING + 1048575) / 1048576 ))
    fi

    PART_FILE="/tmp/hcp-test-part-${i}.bin"
    dd if=/tmp/hcp-test-large.bin of="$PART_FILE" \
        bs=1M skip=$SKIP count=$COUNT 2>/dev/null

    PART_SIZE=$(stat --format=%s "$PART_FILE" 2>/dev/null || stat -f%z "$PART_FILE" 2>/dev/null)
    echo "  Uploading part ${i}/${NUM_PARTS} (${PART_SIZE} bytes)..."

    ETAG=$(aws s3api upload-part $E "$HCP_ENDPOINT" $V \
        --bucket "${BUCKET_NAME}" \
        --key "test-large.bin" \
        --upload-id "$UPLOAD_ID" \
        --part-number "$i" \
        --body "$PART_FILE" \
        --query 'ETag' --output text 2>/dev/null) || { UPLOAD_OK=false; break; }

    echo "    ETag: ${ETAG}"

    [ "$i" -gt 1 ] && PARTS_JSON+=","
    PARTS_JSON+="{\"ETag\":${ETAG},\"PartNumber\":${i}}"

    rm -f "$PART_FILE"
done
PARTS_JSON+="]"

# Complete multipart upload
if $UPLOAD_OK; then
    echo "  Completing multipart upload..."
    if aws s3api complete-multipart-upload $E "$HCP_ENDPOINT" $V \
        --bucket "${BUCKET_NAME}" \
        --key "test-large.bin" \
        --upload-id "$UPLOAD_ID" \
        --multipart-upload "{\"Parts\":${PARTS_JSON}}" 2>&1; then
        ok "Multipart upload completed in ${SECONDS}s"
    else
        fail "Complete multipart failed"
    fi
else
    echo "  Part upload failed — aborting..."
    aws s3api abort-multipart-upload $E "$HCP_ENDPOINT" $V \
        --bucket "${BUCKET_NAME}" \
        --key "test-large.bin" \
        --upload-id "$UPLOAD_ID" 2>&1 || true
    fail "Multipart upload aborted"
fi
