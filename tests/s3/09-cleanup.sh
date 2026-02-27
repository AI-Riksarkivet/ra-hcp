#!/usr/bin/env bash
# Delete test objects and bucket from HCP S3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Listing objects in '${BUCKET_NAME}'..."
aws s3api list-objects-v2 $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" \
    --query 'Contents[].{Key:Key,Size:Size}' --output table 2>&1 || true

echo "Deleting objects..."
aws s3api delete-object $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" --key "test-small.txt" 2>&1 || true
aws s3api delete-object $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" --key "test-large.bin" 2>&1 || true

echo "Deleting bucket '${BUCKET_NAME}'..."
if aws s3api delete-bucket $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" 2>&1; then
    ok "Bucket deleted"
else
    echo "  Bucket delete failed (may need manual cleanup)"
fi

rm -f /tmp/hcp-test-small.txt /tmp/hcp-test-small-dl.txt \
      /tmp/hcp-test-large.bin /tmp/hcp-test-large-dl.bin \
      /tmp/hcp-test-part-*.bin
