# ──────────────────────────────────────────────────────────────────────
#  HCP App — Development commands
# ──────────────────────────────────────────────────────────────────────
SHELL := /bin/bash

.PHONY: help setup install-deno install-uv skills \
        run-api run-api-mock \
        frontend-install frontend-dev frontend-build frontend-check \
        redis redis-stop redis-cli

## help: list available targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  make /' | sed 's/: /\t/'

# ── Setup ────────────────────────────────────────────────────────────

## setup: install all tooling (Deno + uv) and dependencies
setup: install-deno install-uv
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

## skills: show Claude Code skill install guide
skills:
	@cat .claude/README.md

# ── API ──────────────────────────────────────────────────────────────

## run-api: start the HCP API server
# Pass ROOT_PATH for reverse-proxy setups:
#   make run-api ROOT_PATH=/@user/workspace.main/apps/code-server/proxy/8000
ROOT_PATH ?=
run-api:
	cd backend && ROOT_PATH=$(ROOT_PATH) uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 $(if $(ROOT_PATH),--root-path $(ROOT_PATH))

## run-api-mock: start mock dev server (login: admin/password)
run-api-mock:
	cd backend && uv run python mock_server.py

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
