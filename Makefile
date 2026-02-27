# ──────────────────────────────────────────────────────────────────────
#  HCP CLI — Test orchestrator
# ──────────────────────────────────────────────────────────────────────
SHELL := /bin/bash

TESTS_S3 := tests/s3

# Default bucket name (overridable: make test-s3 BUCKET=my-bucket)
BUCKET ?= test-bucket-$(shell date +%s)

# Export so all scripts share the same bucket
export BUCKET_NAME = $(BUCKET)

.PHONY: help run-api test-s3 \
        s3-list s3-create s3-head \
        s3-put s3-get \
        s3-multipart s3-head-object s3-get-large \
        s3-cleanup s3-clean-bucket \
        frontend-install frontend-dev frontend-build frontend-check

## run-api: start the unified HCP API server
## Pass ROOT_PATH for reverse-proxy setups (e.g. code-server proxy):
##   make run-api ROOT_PATH=/@user/workspace.main/apps/code-server/proxy/8000
ROOT_PATH ?=
run-api:
	cd backend && ROOT_PATH=$(ROOT_PATH) uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $(if $(ROOT_PATH),--root-path $(ROOT_PATH))

## help: list available targets
help:
	@echo "HCP S3 test targets:"
	@echo ""
	@echo "  make test-s3              Run full S3 test suite (create, test, cleanup)"
	@echo "  make test-s3 BUCKET=name  Run full suite with a specific bucket name"
	@echo ""
	@echo "  make s3-list              List existing buckets"
	@echo "  make s3-create            Create test bucket"
	@echo "  make s3-head              Verify bucket exists (HEAD)"
	@echo "  make s3-put               Upload small object"
	@echo "  make s3-get               Download small object"
	@echo "  make s3-multipart         Multipart upload test"
	@echo "  make s3-head-object       Verify large object (HEAD)"
	@echo "  make s3-get-large         Download large object"
	@echo "  make s3-cleanup           Delete objects and bucket"
	@echo ""
	@echo "  make s3-clean-bucket BUCKET=name   Clean a specific bucket"
	@echo ""
	@echo "Required env vars: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"

## test-s3: run the full S3 test suite sequentially (cleanup on failure)
test-s3:
	@echo "════════════════════════════════════════════════════════"
	@echo "  HCP S3 Test Suite"
	@echo "════════════════════════════════════════════════════════"
	@echo "  Bucket: $(BUCKET_NAME)"
	@echo ""
	@cleanup() { \
		echo ""; \
		echo "Running cleanup..."; \
		$(TESTS_S3)/09-cleanup.sh || true; \
	}; \
	trap cleanup EXIT; \
	$(TESTS_S3)/01-list-buckets.sh && echo "" && \
	$(TESTS_S3)/02-create-bucket.sh && echo "" && \
	$(TESTS_S3)/03-head-bucket.sh && echo "" && \
	$(TESTS_S3)/04-put-object.sh && echo "" && \
	$(TESTS_S3)/05-get-object.sh && echo "" && \
	$(TESTS_S3)/06-multipart-upload.sh && echo "" && \
	$(TESTS_S3)/07-head-object.sh && echo "" && \
	$(TESTS_S3)/08-get-object-large.sh && echo "" && \
	echo "" && \
	echo "════════════════════════════════════════════════════════" && \
	echo "  All tests passed!" && \
	echo "════════════════════════════════════════════════════════"

## s3-list: list existing buckets
s3-list:
	@$(TESTS_S3)/01-list-buckets.sh

## s3-create: create test bucket
s3-create:
	@$(TESTS_S3)/02-create-bucket.sh

## s3-head: verify bucket exists
s3-head:
	@$(TESTS_S3)/03-head-bucket.sh

## s3-put: upload small object
s3-put:
	@$(TESTS_S3)/04-put-object.sh

## s3-get: download small object
s3-get:
	@$(TESTS_S3)/05-get-object.sh

## s3-multipart: multipart upload test
s3-multipart:
	@$(TESTS_S3)/06-multipart-upload.sh

## s3-head-object: verify large object
s3-head-object:
	@$(TESTS_S3)/07-head-object.sh

## s3-get-large: download large object
s3-get-large:
	@$(TESTS_S3)/08-get-object-large.sh

## s3-cleanup: delete objects and bucket
s3-cleanup:
	@$(TESTS_S3)/09-cleanup.sh

## s3-clean-bucket: clean a specific orphaned bucket
s3-clean-bucket:
	@test -n "$(BUCKET)" || { echo "Usage: make s3-clean-bucket BUCKET=name"; exit 1; }
	@$(TESTS_S3)/09-cleanup.sh

# ── Frontend ─────────────────────────────────────────────────────────

## frontend-install: install frontend dependencies
frontend-install:
	cd frontend && deno install

## frontend-dev: start the frontend dev server
frontend-dev:
	cd frontend && BACKEND_URL=http://localhost:8000 deno task dev

## frontend-build: build the frontend for production
frontend-build:
	cd frontend && deno task build

## frontend-check: run type checking on the frontend
frontend-check:
	cd frontend && deno task check
