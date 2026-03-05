package main

import (
	"context"

	"dagger/hcp-app/internal/dagger"
)

// Serve starts the backend as a Dagger service on port 8000 with Redis.
func (m *HcpApp) Serve(source *dagger.Directory) *dagger.Service {
	redisSvc := m.redis()

	return m.BuildBackend(source).
		WithServiceBinding("redis", redisSvc).
		WithEnvVariable("REDIS_URL", "redis://redis:6379").
		WithExposedPort(8000).
		AsService()
}

// ServeAll starts the full stack: Redis, backend (:8000), and frontend (:8000).
// The frontend Deno server defaults to port 8000; use `up --ports 3000:8000`
// to expose it on host port 3000.
func (m *HcpApp) ServeAll(source *dagger.Directory) *dagger.Service {
	backendSvc := m.Serve(source)

	return m.BuildFrontend(source).
		WithServiceBinding("backend", backendSvc).
		WithEnvVariable("BACKEND_URL", "http://backend:8000").
		WithExposedPort(8000).
		AsService()
}

// TestServer starts the backend and verifies it responds to a health check.
func (m *HcpApp) TestServer(ctx context.Context, source *dagger.Directory) (string, error) {
	svc := m.Serve(source)

	return dag.Container().From("alpine:3.21").
		WithServiceBinding("backend", svc).
		WithExec([]string{"wget", "-qO-", "http://backend:8000/health"}).
		Stdout(ctx)
}
