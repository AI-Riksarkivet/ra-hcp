# ra-hcp

[![Tests](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/ci.yml)
[![Docs](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/docs.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/docs.yml)
[![Storybook](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/storybook.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/storybook.yml)
[![CodeQL](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/codeql.yml)
[![Scorecard](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/scorecard.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/scorecard.yml)
[![TruffleHog](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/trufflehog.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-hcp/actions/workflows/trufflehog.yml)

Web application for managing Hitachi Content Platform (HCP) — S3-compatible object storage and Management API operations.

| Layer | Technology |
|-------|------------|
| Frontend | SvelteKit 2, Svelte 5, Tailwind CSS 4, Bun |
| Backend | FastAPI, boto3, Python, uv |
| Caching | Redis |
| Docs | Zensical |
| CI/CD | Dagger, Docker, Helm |

## Quick Start

```bash
make setup          # Install Bun + uv and all dependencies
make run-api-mock   # Start mock backend (no HCP credentials needed)
make frontend-dev   # Start frontend dev server
```

For production mode with real HCP credentials: `make run-api`

## Documentation

- [Docs site](https://ai-riksarkivet.github.io/hcp/) — architecture, API guide, configuration
- [Storybook](https://ai-riksarkivet.github.io/hcp/storybook/) — component library

## Requirements

- [Bun](https://bun.sh) — frontend runtime
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Docker — for Redis caching (optional)


## Gallery

<img width="2523" height="1298" alt="image" src="https://github.com/user-attachments/assets/e3e27ebf-5901-4c41-8d68-0d12a13f2d97" />

<img width="2534" height="1317" alt="image" src="https://github.com/user-attachments/assets/43ec04b3-2fcc-4b49-b2b1-26ea70d3fd17" />

<img width="2530" height="1253" alt="image" src="https://github.com/user-attachments/assets/9098e9f9-2778-42ba-9c13-24f6259c0a69" />

