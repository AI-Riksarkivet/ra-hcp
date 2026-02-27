#!/usr/bin/env bash
# Download a small object from HCP S3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Downloading small object (s3api get-object)..."
if aws s3api get-object $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" \
    --key "test-small.txt" \
    /tmp/hcp-test-small-dl.txt 2>&1; then
    ok "Content: $(cat /tmp/hcp-test-small-dl.txt)"
else
    fail "Download failed"
fi
