package main

import (
	"context"

	"dagger/hcp-app/internal/dagger"
)

// RuffCheck runs ruff linting on the backend.
func (m *HcpApp) RuffCheck(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "ruff", "check", "."}).
		Stdout(ctx)
}

// RuffFormat checks that backend code is formatted with ruff.
func (m *HcpApp) RuffFormat(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "ruff", "format", "--check", "."}).
		Stdout(ctx)
}

// TypeCheck runs mypy on the backend.
func (m *HcpApp) TypeCheck(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "mypy", "."}).
		Stdout(ctx)
}

// FrontendCheck runs type-checking on the frontend.
func (m *HcpApp) FrontendCheck(ctx context.Context, source *dagger.Directory) (string, error) {
	frontend := source.Directory(frontendDir)

	return dag.Container().From(denoImage).
		WithMountedDirectory("/app", frontend).
		WithWorkdir("/app").
		WithExec([]string{"deno", "install"}).
		WithExec([]string{"deno", "task", "check"}).
		Stdout(ctx)
}

// Checks runs all code quality checks (ruff, mypy, frontend) in parallel.
func (m *HcpApp) Checks(ctx context.Context, source *dagger.Directory) (string, error) {
	// Run all checks — each call is independently cached by Dagger
	_, err := m.RuffCheck(ctx, source)
	if err != nil {
		return "", err
	}

	_, err = m.RuffFormat(ctx, source)
	if err != nil {
		return "", err
	}

	_, err = m.TypeCheck(ctx, source)
	if err != nil {
		return "", err
	}

	_, err = m.FrontendCheck(ctx, source)
	if err != nil {
		return "", err
	}

	return "All checks passed", nil
}
