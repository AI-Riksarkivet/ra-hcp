#!/usr/bin/env bash
# Verify large object exists on HCP S3 (HEAD request)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Verifying large object exists (HEAD)..."
if aws s3api head-object $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" \
    --key "test-large.bin" \
    --query '[ContentLength, ETag]' --output text 2>&1; then
    ok "Object confirmed on HCP"
else
    fail "Object not found"
fi
