# HCP App

[![Tests](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/ci.yml)
[![Documentation](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/docs.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/docs.yml)
[![Storybook](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/storybook.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/storybook.yml)
[![CodeQL](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/codeql.yml)
[![Scorecard](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/scorecard.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/scorecard.yml)
[![TruffleHog](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/trufflehog.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/trufflehog.yml)

Hitachi Content Platform (HCP) application — unified web app for S3-compatible object storage and HCP Management API operations.

## Project Structure

```
hcp/
├── backend/          # FastAPI API server (Python, uv)
├── frontend/         # SvelteKit 2 + Svelte 5 frontend (Deno)
├── docs/             # Zensical documentation site
├── charts/           # Helm charts for Kubernetes
├── .dagger/          # Dagger CI/CD
├── .docker/          # Docker Compose files
└── Makefile          # Development commands
```

## Quick Start

### 1. Install tooling

```bash
# Install everything (Deno + uv) and all dependencies
make setup
```

Or install individually:

```bash
make install-deno    # Deno runtime (frontend)
make install-uv      # uv package manager (backend)
```

### 2. Claude Code skills

The project uses Claude Code skills for development assistance (`.claude/settings.json`):

```jsonc
{
  "enabledPlugins": {
    "svelte-skills@svelte-skills-kit": true,       // Svelte 5 / SvelteKit 2
    "deno-skills@denoland-skills": true,            // Deno runtime
    "mcp-essentials@claude-code-toolkit": true,     // Core toolkit
    "analytics@claude-code-toolkit": true,          // Analytics
    "toolkit-skills@claude-code-toolkit": true,     // General toolkit
    "redis-development@redis": true                 // Redis
  }
}
```

These are already configured — no action needed if cloning this repo.

### 3. Start the backend

```bash
# Production-like (requires HCP credentials)
make run-api

# With reverse-proxy root path
make run-api ROOT_PATH=/proxy/8000

# Mock server (no credentials needed, login: admin/password)
make run-api-mock
```

### 4. Start the frontend

```bash
make frontend-install   # Install dependencies (deno install)
make frontend-dev       # Start dev server (connects to localhost:8000)
```

### 5. Redis (optional, for caching)

```bash
make redis              # Start Redis via Docker Compose
make redis-stop         # Stop Redis
make redis-cli          # Open Redis CLI
```

## Tech Stack

| Layer         | Technology                                    |
|---------------|-----------------------------------------------|
| Frontend      | Deno, SvelteKit 2, Svelte 5, Tailwind CSS 4  |
| Backend       | Python, FastAPI, boto3, uv                    |
| Caching       | Redis                                         |
| Docs          | Zensical                                      |
| CI/CD         | Dagger, Docker, Helm                          |

## All Make Targets

```bash
make help
```

## Requirements

- [Deno](https://deno.com) (frontend)
- [uv](https://docs.astral.sh/uv/) (backend)
- Docker (for Redis)
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (for production API)
