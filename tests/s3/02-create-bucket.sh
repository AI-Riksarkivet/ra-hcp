#!/usr/bin/env bash
# Create an HCP S3 bucket
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Creating bucket '${BUCKET_NAME}'..."
if aws s3api create-bucket $E "$HCP_ENDPOINT" $V \
    --bucket "${BUCKET_NAME}" 2>&1; then
    ok "Bucket created"
else
    fail "Failed to create bucket"
fi
