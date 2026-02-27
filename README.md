# HCP App

Hitachi Content Platform (HCP) application for S3-compatible object storage operations.

## Project Structure

```
hcp-app/
├── backend/          # FastAPI-based S3 API service
├── frontend/         # Frontend application
├── tests/            # Test suites (S3, etc.)
├── docs/
│   └── hcp_docs/     # HCP documentation (S3, NFS, MAPI)
└── Makefile          # Test orchestrator & dev commands
```

## Quick Start

### Run the API server

```bash
make run-api
```

With a reverse-proxy root path:

```bash
make run-api ROOT_PATH=/proxy/8000
```

### Run S3 tests

```bash
# Full test suite
make test-s3

# With a specific bucket name
make test-s3 BUCKET=my-bucket
```

### Available Make targets

```bash
make help
```

## Requirements

- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- See `.env` for configuration
