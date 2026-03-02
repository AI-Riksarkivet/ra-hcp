// HCP App CI/CD pipeline powered by Dagger
//
// Provides build, lint, type-check, and test functions for the
// hcp-app backend (Python/FastAPI) and frontend (SvelteKit/Deno).

package main

import (
	"dagger/hcp-app/internal/dagger"
)

const (
	pythonImage = "python:3.14-slim"
	denoImage   = "denoland/deno:latest"
	backendDir  = "backend"
	frontendDir = "frontend"
)

type HcpApp struct{}

// withUv returns a Python container with uv pre-installed.
func (m *HcpApp) withUv(base *dagger.Container) *dagger.Container {
	return base.
		WithExec([]string{"pip", "install", "--quiet", "uv"})
}

// buildBackendDev returns a container with all backend deps (including dev) installed.
func (m *HcpApp) buildBackendDev(source *dagger.Directory) *dagger.Container {
	backend := source.Directory(backendDir)

	return m.withUv(dag.Container().From(pythonImage)).
		WithMountedDirectory("/app", backend).
		WithWorkdir("/app").
		WithExec([]string{"uv", "sync", "--frozen"})
}
