// HCP App CI/CD pipeline powered by Dagger
//
// Provides build, lint, type-check, and test functions for the
// hcp-app backend (Python/FastAPI) and frontend (SvelteKit/Deno).

package main

import (
	"dagger/hcp-app/internal/dagger"
)

const (
	uvPythonImage = "ghcr.io/astral-sh/uv:0.10.9-python3.13-trixie-slim"
	denoImage     = "denoland/deno:2.7.1"
	redisImage    = "redis:8.0.1-alpine"
	backendDir    = "backend"
	frontendDir   = "frontend"
)

type HcpApp struct{}

// buildBackendDev returns a container with all backend deps (including dev) installed.
func (m *HcpApp) buildBackendDev(source *dagger.Directory) *dagger.Container {
	backend := source.Directory(backendDir)

	return dag.Container().From(uvPythonImage).
		WithMountedCache("/root/.cache/uv", dag.CacheVolume("uv-cache")).
		WithMountedDirectory("/app", backend).
		WithWorkdir("/app").
		WithExec([]string{"uv", "sync", "--frozen", "--extra", "lance"})
}

// buildFrontendDev returns a Deno container with frontend deps installed.
func (m *HcpApp) buildFrontendDev(source *dagger.Directory) *dagger.Container {
	frontend := source.Directory(frontendDir)

	return dag.Container().From(denoImage).
		WithEnvVariable("DENO_DIR", "/deno-dir").
		WithMountedCache("/deno-dir", dag.CacheVolume("deno-cache")).
		WithMountedDirectory("/app", frontend).
		WithWorkdir("/app").
		WithExec([]string{"deno", "install"})
}

// redis returns a Redis service for integration tests.
func (m *HcpApp) redis() *dagger.Service {
	return dag.Container().From(redisImage).
		WithExposedPort(6379).
		AsService()
}
