#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
#  Shared configuration for HCP S3 test scripts
# ──────────────────────────────────────────────────────────────────────
#
#  HCP S3 auth:
#    AWS_ACCESS_KEY_ID     = base64(username)
#    AWS_SECRET_ACCESS_KEY = md5(password)
#
#  Source this file from each test script:
#    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#    source "${SCRIPT_DIR}/common.sh"
#
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── HCP endpoint ──────────────────────────────────────────────────────
HCP_TENANT="dev-ai"
HCP_DOMAIN="hcp.ra-dev.int"
HCP_ENDPOINT="https://${HCP_TENANT}.${HCP_DOMAIN}"

# ── AWS credentials ──────────────────────────────────────────────────
AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:?Set AWS_ACCESS_KEY_ID (base64 encoded username)}"
AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:?Set AWS_SECRET_ACCESS_KEY (md5 hashed password)}"
export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION="us-east-1"

# ── Bucket name (shared across scripts) ──────────────────────────────
BUCKET_NAME="${BUCKET_NAME:?Set BUCKET_NAME}"

# ── Multipart settings ───────────────────────────────────────────────
MULTIPART_FILE_SIZE_MB="${MULTIPART_FILE_SIZE_MB:-15}"
CHUNK_SIZE_MB="${CHUNK_SIZE_MB:-5}"
CHUNK_SIZE_BYTES=$(( CHUNK_SIZE_MB * 1024 * 1024 ))

# ── AWS CLI config ───────────────────────────────────────────────────
# Point to the repo-level .aws/config (path-style + sigv4, no checksums)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export AWS_CONFIG_FILE="${REPO_ROOT}/.aws/config"

# ── Common CLI flags ─────────────────────────────────────────────────
E="--endpoint-url"
V="--no-verify-ssl"

# ── Helpers ──────────────────────────────────────────────────────────
ok()   { echo "  OK: $*"; }
fail() { echo "  FAIL: $*"; return 1; }
