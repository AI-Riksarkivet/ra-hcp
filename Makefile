# ──────────────────────────────────────────────────────────────────────
#  HCP App — Development commands
# ──────────────────────────────────────────────────────────────────────
SHELL := /bin/bash
export PATH := $(HOME)/.bun/bin:$(PATH)

.PHONY: help setup install-bun install-uv setup-hooks skills \
        fmt lint quality \
        run-api run-api-mock \
        frontend-dev frontend-build storybook build-storybook test-storybook \
        docs docs-build \
        checks test test-integration e2e serve-backend full-serve build \
        scan scan-backend scan-frontend scan-image \
        publish publish-backend publish-frontend

## help: list available targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | sed 's/: /\t/'

# ── Setup ────────────────────────────────────────────────────────────

## setup: install all tooling, dependencies, and git hooks
setup: install-bun install-uv setup-hooks
	cd backend && uv sync --extra serve
	cd frontend && bun install
	@echo ""
	@echo "For Claude Code skills, see: .claude/README.md"

## install-bun: install Bun runtime
install-bun:
	@command -v bun >/dev/null 2>&1 || curl -fsSL https://bun.sh/install | bash

## install-uv: install uv (Python package manager)
install-uv:
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh

## setup-hooks: install git pre-commit hook
setup-hooks:
	ln -sf ../../.claude/hooks/pre-commit .git/hooks/pre-commit
	@echo "Git pre-commit hook installed."

## skills: show Claude Code skill install guide
skills:
	@cat .claude/README.md

# ── Quality ──────────────────────────────────────────────────────────

## fmt: format all code (backend + frontend)
fmt:
	cd backend && uvx ruff format .
	cd frontend && bun run format

## lint: lint all code (backend + frontend)
lint:
	cd backend && uvx ruff check .
	cd frontend && bun run check

## quality: format, lint, and type-check everything
quality: fmt lint
	cd frontend && bun run check || echo "Warning: frontend type errors (see above)"
	cd backend && uvx ty check || echo "Warning: backend type errors (see above)"

# ── API ──────────────────────────────────────────────────────────────

## run-api: start the HCP API server
ROOT_PATH ?=
run-api:
	cd backend && ROOT_PATH=$(ROOT_PATH) uv run --extra serve uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $(if $(ROOT_PATH),--root-path $(ROOT_PATH))

## run-api-mock: start mock dev server (login: admin/password)
run-api-mock:
	cd backend && uv run --extra serve uvicorn mock_server:app --reload --host 0.0.0.0 --port 8000

# ── Frontend ─────────────────────────────────────────────────────────

## frontend-dev: start the frontend dev server
frontend-dev:
	cd frontend && BACKEND_URL=http://127.0.0.1:8000 bun run dev

## frontend-build: build the frontend for production
frontend-build:
	cd frontend && bun run build

## storybook: start Storybook dev server on port 6006
storybook:
	cd frontend && bun run storybook

## build-storybook: build Storybook static site
build-storybook:
	cd frontend && bun run build-storybook

## test-storybook: run Storybook interaction + a11y tests via Vitest
test-storybook:
	cd frontend && bun run test-storybook

# ── Docs ─────────────────────────────────────────────────────────────

## docs: serve documentation site locally (live-reload)
docs:
	PYTHONPATH=backend uvx --with mkdocstrings-python zensical serve

## docs-build: build documentation site for deployment
docs-build:
	PYTHONPATH=backend uvx --with mkdocstrings-python zensical build --clean

# ── Dagger ───────────────────────────────────────────────────────────

## checks: run all lint & type-checks in Dagger
checks:
	dagger call checks --source=.

## test: run unit tests with coverage in Dagger
test:
	dagger call test-coverage --source=.

## test-integration: run integration tests (real Redis) in Dagger
test-integration:
	dagger call test-integration --source=.

## e2e: full-stack Playwright smoke test (browser -> frontend -> backend -> S3/MinIO) in Dagger
e2e:
	dagger call end-to-end --source=.

## serve-backend: start backend + Redis in Dagger on :8000
serve-backend:
	dagger call serve --source=. up --ports 8000:8000

## full-serve: start full stack in Dagger — frontend on :5174, backend internal
full-serve:
	dagger call serve-all --source=. up --ports 5174:8000

## build: build backend and frontend containers in Dagger
build:
	dagger call build-backend --source=.
	dagger call build-frontend --source=.

# ── Security / CVE scanning ──────────────────────────────────────────
# Trivy (github.com/jpadams/daggerverse/trivy) scans built images for known
# CVEs inside Dagger. By default these are report-only (exit-code 0) and print
# the full HIGH/CRITICAL vulnerability table. To gate a release — fail on any
# HIGH/CRITICAL finding — append EXIT_CODE=1, e.g. `make scan EXIT_CODE=1`.
EXIT_CODE ?= 0

## scan: Trivy CVE scan of both backend + frontend images
scan:
	dagger call scan --source=. --exit-code=$(EXIT_CODE)

## scan-backend: Trivy CVE scan of the backend image
scan-backend:
	dagger call scan-backend --source=. --exit-code=$(EXIT_CODE)

## scan-frontend: Trivy CVE scan of the frontend image
scan-frontend:
	dagger call scan-frontend --source=. --exit-code=$(EXIT_CODE)

## scan-image: Trivy CVE scan of a published image ref (IMAGE=repo:tag)
scan-image:
	dagger call scan-image --image-ref=$(IMAGE) --exit-code=$(EXIT_CODE)

# ── Publish ──────────────────────────────────────────────────────────
TAG ?= v0.2.0

## publish: publish both backend and frontend images to Docker Hub
publish:
	@DOCKER_USERNAME=$$(grep '^DOCKER_USERNAME=' .env | cut -d= -f2 | tr -d '"') \
	DOCKER_PASSWORD=$$(grep '^DOCKER_PASSWORD=' .env | cut -d= -f2 | tr -d '"') \
	dagger call publish-all --source=. --tag=$(TAG) \
		--docker-username=env:DOCKER_USERNAME \
		--docker-password=env:DOCKER_PASSWORD

## publish-backend: publish backend image to Docker Hub
publish-backend:
	@DOCKER_USERNAME=$$(grep '^DOCKER_USERNAME=' .env | cut -d= -f2 | tr -d '"') \
	DOCKER_PASSWORD=$$(grep '^DOCKER_PASSWORD=' .env | cut -d= -f2 | tr -d '"') \
	dagger call publish-backend --source=. --tag=$(TAG) \
		--docker-username=env:DOCKER_USERNAME \
		--docker-password=env:DOCKER_PASSWORD

## publish-frontend: publish frontend image to Docker Hub
publish-frontend:
	@DOCKER_USERNAME=$$(grep '^DOCKER_USERNAME=' .env | cut -d= -f2 | tr -d '"') \
	DOCKER_PASSWORD=$$(grep '^DOCKER_PASSWORD=' .env | cut -d= -f2 | tr -d '"') \
	dagger call publish-frontend --source=. --tag=$(TAG) \
		--docker-username=env:DOCKER_USERNAME \
		--docker-password=env:DOCKER_PASSWORD
