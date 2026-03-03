# ──────────────────────────────────────────────────────────────────────
#  HCP App — Development commands
# ──────────────────────────────────────────────────────────────────────
SHELL := /bin/bash
export PATH := $(HOME)/.deno/bin:$(PATH)

.PHONY: help setup install-deno install-uv setup-hooks skills \
        fmt lint quality \
        run-api run-api-mock \
        frontend-dev frontend-build \
        redis redis-stop redis-cli

## help: list available targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | sed 's/: /\t/'

# ── Setup ────────────────────────────────────────────────────────────

## setup: install all tooling, dependencies, and git hooks
setup: install-deno install-uv setup-hooks
	cd backend && uv sync
	cd frontend && deno install
	@echo ""
	@echo "For Claude Code skills, see: .claude/README.md"

## install-deno: install Deno runtime
install-deno:
	@command -v deno >/dev/null 2>&1 || curl -fsSL https://deno.land/install.sh | sh

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
	cd frontend && deno task fmt

## lint: lint all code (backend + frontend)
lint:
	cd backend && uvx ruff check .
	cd frontend && deno lint

## quality: format, lint, and type-check everything
quality: fmt lint
	cd frontend && deno task check || echo "Warning: frontend type errors (see above)"
	cd backend && uvx ty check || echo "Warning: backend type errors (see above)"

# ── API ──────────────────────────────────────────────────────────────

## run-api: start the HCP API server
ROOT_PATH ?=
run-api:
	cd backend && ROOT_PATH=$(ROOT_PATH) uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $(if $(ROOT_PATH),--root-path $(ROOT_PATH))

## run-api-mock: start mock dev server (login: admin/password)
run-api-mock:
	cd backend && uv run python mock_server.py

# ── Frontend ─────────────────────────────────────────────────────────

## frontend-dev: start the frontend dev server
frontend-dev:
	cd frontend && BACKEND_URL=http://localhost:8000 deno task dev

## frontend-build: build the frontend for production
frontend-build:
	cd frontend && deno task build

# ── Redis ────────────────────────────────────────────────────────────

## redis: start Redis via Docker Compose (required for caching)
redis:
	docker compose -f .docker/docker-compose.yml up -d redis

## redis-stop: stop Redis
redis-stop:
	docker compose -f .docker/docker-compose.yml down

## redis-cli: open a Redis CLI session
redis-cli:
	docker compose -f .docker/docker-compose.yml exec redis redis-cli
