#!/usr/bin/env bash
# Verify an HCP S3 bucket exists (HEAD request)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Verifying bucket '${BUCKET_NAME}' exists (HEAD)..."
if aws s3api head-bucket $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" 2>&1; then
    ok "Bucket confirmed"
else
    fail "Bucket not found"
fi
