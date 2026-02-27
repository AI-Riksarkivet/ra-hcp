#!/usr/bin/env bash
# Upload a small object to HCP S3 (single PUT)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Uploading small object (s3api put-object)..."
echo "Hello from HCP S3 test — $(date)" > /tmp/hcp-test-small.txt
if aws s3api put-object $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" \
    --key "test-small.txt" \
    --body /tmp/hcp-test-small.txt 2>&1; then
    ok "Small object uploaded"
else
    fail "Small upload failed"
fi
