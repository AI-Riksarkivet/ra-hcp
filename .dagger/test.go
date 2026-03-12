package main

import (
	"context"

	"dagger/ra-hcp/internal/dagger"
)

// Test runs pytest on the backend.
func (m *RaHcp) Test(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "pytest"}).
		Stdout(ctx)
}

// TestCoverage runs pytest with coverage reporting.
func (m *RaHcp) TestCoverage(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "pytest", "--cov"}).
		Stdout(ctx)
}

// TestIntegration runs integration tests with a real Redis service.
func (m *RaHcp) TestIntegration(ctx context.Context, source *dagger.Directory) (string, error) {
	redisSvc := m.redis()

	return m.buildBackendDev(source).
		WithServiceBinding("redis", redisSvc).
		WithEnvVariable("REDIS_URL", "redis://redis:6379").
		WithExec([]string{"uv", "run", "pytest", "-m", "redis"}).
		Stdout(ctx)
}
