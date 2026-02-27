#!/usr/bin/env bash
# List existing HCP S3 buckets
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

echo "Listing existing buckets..."
aws s3api list-buckets $E "$HCP_ENDPOINT" $V \
    --query 'Buckets[].Name' --output table 2>&1 || echo "  Could not list buckets"
