package main

import (
	"bufio"
	"context"
	"strings"

	"dagger/ra-hcp/internal/dagger"
)

// skipKeys are env vars managed by Dagger (service bindings) or intercepted
// by the Dagger telemetry pipeline. These must not be set from .env.
var skipKeys = map[string]bool{
	"REDIS_URL":   true,
	"BACKEND_URL": true,
}

// skipPrefixes are env var prefixes that Dagger intercepts and routes
// through its own telemetry collector, causing metric format errors.
var skipPrefixes = []string{"OTEL_", "DAGGER_"}

// applyEnvFile reads a .env file and sets each KEY=VALUE on the container.
// Lines starting with # and empty lines are skipped. Surrounding quotes
// on values are stripped. Keys in skipKeys and skipPrefixes are skipped.
func applyEnvFile(ctx context.Context, ctr *dagger.Container, envFile *dagger.File) (*dagger.Container, error) {
	contents, err := envFile.Contents(ctx)
	if err != nil {
		return nil, err
	}
	scanner := bufio.NewScanner(strings.NewReader(contents))
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, val, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key = strings.TrimSpace(key)
		val = strings.TrimSpace(val)
		// Strip surrounding quotes
		if len(val) >= 2 && ((val[0] == '"' && val[len(val)-1] == '"') || (val[0] == '\'' && val[len(val)-1] == '\'')) {
			val = val[1 : len(val)-1]
		}
		if key == "" || skipKeys[key] {
			continue
		}
		skip := false
		for _, prefix := range skipPrefixes {
			if strings.HasPrefix(key, prefix) {
				skip = true
				break
			}
		}
		if skip {
			continue
		}
		ctr = ctr.WithEnvVariable(key, val)
	}
	return ctr, nil
}

// Serve starts the backend as a Dagger service on port 8000 with Redis.
func (m *RaHcp) Serve(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// +optional
	// +defaultPath=".env"
	envFile *dagger.File,
) (*dagger.Service, error) {
	redisSvc := m.redis()

	ctr := m.BuildBackend(source)

	// Apply .env first (HCP connection settings, cache config, etc.)
	if envFile != nil {
		var err error
		ctr, err = applyEnvFile(ctx, ctr, envFile)
		if err != nil {
			return nil, err
		}
	}

	// Disable OTEL metrics export — Dagger intercepts OTEL env vars and
	// routes through its own collector which returns 500 for app metrics.
	ctr = ctr.WithEnvVariable("OTEL_METRICS_EXPORTER", "none")

	// Dagger-managed overrides (service bindings) — always last
	ctr = ctr.
		WithServiceBinding("redis", redisSvc).
		WithEnvVariable("REDIS_URL", "redis://redis:6379")

	return ctr.
		WithExposedPort(8000).
		AsService(), nil
}

// ServeFrontend starts the frontend as a Dagger service exposed on port 5174.
// Internally the Deno server listens on 8000; a socat proxy maps 5174→8000.
func (m *RaHcp) ServeFrontend(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// +optional
	// +defaultPath=".env"
	envFile *dagger.File,
) (*dagger.Service, error) {
	backendSvc, err := m.Serve(ctx, source, envFile)
	if err != nil {
		return nil, err
	}

	frontendSvc := m.BuildFrontend(source).
		WithServiceBinding("backend", backendSvc).
		WithEnvVariable("BACKEND_URL", "http://backend:8000").
		WithExposedPort(8000).
		AsService()

	// Expose frontend on 5174 via proxy
	return dag.Container().
		From("alpine:3.21").
		WithExec([]string{"apk", "add", "--no-cache", "socat"}).
		WithServiceBinding("frontend", frontendSvc).
		WithExposedPort(5174).
		WithExec([]string{"socat", "TCP-LISTEN:5174,fork,reuseaddr", "TCP:frontend:8000"}).
		AsService(), nil
}

// ServeAll starts the full stack: Redis, backend (:8000), and frontend (:5174).
// Both services are exposed via a lightweight proxy.
func (m *RaHcp) ServeAll(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// +optional
	// +defaultPath=".env"
	envFile *dagger.File,
) (*dagger.Service, error) {
	backendSvc, err := m.Serve(ctx, source, envFile)
	if err != nil {
		return nil, err
	}

	frontendSvc := m.BuildFrontend(source).
		WithServiceBinding("backend", backendSvc).
		WithEnvVariable("BACKEND_URL", "http://backend:8000").
		WithExposedPort(8000).
		AsService()

	// Proxy binds both services and maps:
	//   host:8000 → backend:8000
	//   host:5174 → frontend:8000 (Deno default port)
	return dag.Container().
		From("alpine:3.21").
		WithExec([]string{"apk", "add", "--no-cache", "socat"}).
		WithServiceBinding("backend", backendSvc).
		WithServiceBinding("frontend", frontendSvc).
		WithExposedPort(8000).
		WithExposedPort(5174).
		WithExec([]string{"sh", "-c",
			"socat TCP-LISTEN:8000,fork,reuseaddr TCP:backend:8000 & " +
				"socat TCP-LISTEN:5174,fork,reuseaddr TCP:frontend:8000 & " +
				"wait",
		}).
		AsService(), nil
}

// TestServer starts the backend and verifies it responds to a health check.
func (m *RaHcp) TestServer(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// +optional
	// +defaultPath=".env"
	envFile *dagger.File,
) (string, error) {
	svc, err := m.Serve(ctx, source, envFile)
	if err != nil {
		return "", err
	}

	return dag.Container().From("alpine:3.21").
		WithServiceBinding("backend", svc).
		WithExec([]string{"wget", "-qO-", "http://backend:8000/health"}).
		Stdout(ctx)
}
