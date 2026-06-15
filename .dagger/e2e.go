package main

import (
	"context"

	"dagger/ra-hcp/internal/dagger"
)

// E2e runs the full-stack Playwright smoke test: a real browser drives the
// SvelteKit frontend (SSR + remote functions), which talks to the FastAPI
// backend, which talks to a real S3 server (MinIO) — MAPI disabled (S3-only).
//
// It exercises the one path unit/Storybook tests can't: browser → SSR →
// remote function → backend → S3 write, then read-back. See
// frontend/e2e/s3-smoke.spec.ts.
//
// CLI: `dagger call end-to-end --source=.` (or `make e2e`).
func (m *RaHcp) EndToEnd(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
) (string, error) {
	// S3-only backend (Redis + MinIO wired, MAPI off).
	backendSvc, err := m.ServeMinio(ctx, source, nil)
	if err != nil {
		return "", err
	}

	// Frontend service — svelte-adapter-bun listens on PORT (3000). ORIGIN must
	// match the URL the browser uses, or SvelteKit's CSRF check rejects
	// remote-function POSTs (mutations) with 403.
	frontendSvc := m.BuildFrontend(source).
		WithServiceBinding("backend", backendSvc).
		WithEnvVariable("BACKEND_URL", "http://backend:8000").
		WithEnvVariable("PORT", "3000").
		WithEnvVariable("ORIGIN", "http://frontend:3000").
		WithExposedPort(3000).
		AsService()

	feDir := source.Directory(frontendDir)

	// Playwright runner (Bun-native, consistent with the rest of the stack).
	return dag.Container().From(bunImage).
		WithServiceBinding("frontend", frontendSvc).
		WithEnvVariable("E2E_BASE_URL", "http://frontend:3000").
		WithEnvVariable("CI", "true").
		WithMountedCache("/root/.bun/install/cache", dag.CacheVolume("bun-cache")).
		WithMountedCache("/root/.cache/ms-playwright", dag.CacheVolume("playwright-browsers")).
		WithMountedDirectory("/app", feDir).
		WithWorkdir("/app").
		WithExec([]string{"bun", "install"}).
		WithExec([]string{"bunx", "playwright", "install", "--with-deps", "chromium"}).
		WithExec([]string{"bunx", "playwright", "test"}).
		Stdout(ctx)
}
