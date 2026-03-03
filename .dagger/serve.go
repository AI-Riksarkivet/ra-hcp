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

// ServeAll starts the full stack (Redis, backend, frontend) using docker-compose.
func (m *HcpApp) ServeAll(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
) ([]*dagger.Service, error) {
	project := dag.DockerCompose().Project(dagger.DockerComposeProjectOpts{
		Source: source,
	})

	composeServices, err := project.Services(ctx)
	if err != nil {
		return nil, err
	}

	var services []*dagger.Service
	for _, svc := range composeServices {
		services = append(services, svc.Up())
	}
	return services, nil
}

// TestServer starts the backend and verifies it responds to a health check.
func (m *HcpApp) TestServer(ctx context.Context, source *dagger.Directory) (string, error) {
	svc := m.Serve(source)

	return dag.Container().From("alpine:latest").
		WithServiceBinding("backend", svc).
		WithExec([]string{"wget", "-qO-", "http://backend:8000/health"}).
		Stdout(ctx)
}
