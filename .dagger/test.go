package main

import (
	"context"

	"dagger/hcp-app/internal/dagger"
)

// Test runs pytest on the backend.
func (m *HcpApp) Test(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "pytest"}).
		Stdout(ctx)
}

// TestCoverage runs pytest with coverage reporting.
func (m *HcpApp) TestCoverage(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "pytest", "--cov"}).
		Stdout(ctx)
}
