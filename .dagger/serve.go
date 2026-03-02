package main

import (
	"context"

	"dagger/hcp-app/internal/dagger"
)

// Serve starts the backend as a Dagger service on port 8000.
func (m *HcpApp) Serve(source *dagger.Directory) *dagger.Service {
	return m.BuildBackend(source).
		WithExposedPort(8000).
		AsService()
}

// TestServer starts the backend and verifies it responds to a health check.
func (m *HcpApp) TestServer(ctx context.Context, source *dagger.Directory) (string, error) {
	svc := m.Serve(source)

	return dag.Container().From("alpine:latest").
		WithServiceBinding("backend", svc).
		WithExec([]string{"wget", "-qO-", "http://backend:8000/health"}).
		Stdout(ctx)
}
