package main

import (
	"context"
	"fmt"

	"dagger/hcp-app/internal/dagger"

	"golang.org/x/sync/errgroup"
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

// TypeCheck runs ty on the backend.
func (m *HcpApp) TypeCheck(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildBackendDev(source).
		WithExec([]string{"uv", "run", "ty", "check"}).
		Stdout(ctx)
}

// FrontendCheck runs type-checking on the frontend.
func (m *HcpApp) FrontendCheck(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildFrontendDev(source).
		WithExec([]string{"deno", "task", "check"}).
		Stdout(ctx)
}

// FrontendLint runs deno lint on the frontend.
func (m *HcpApp) FrontendLint(ctx context.Context, source *dagger.Directory) (string, error) {
	return m.buildFrontendDev(source).
		WithExec([]string{"deno", "lint"}).
		Stdout(ctx)
}

// Checks runs all code quality checks in parallel.
func (m *HcpApp) Checks(ctx context.Context, source *dagger.Directory) (string, error) {
	g, ctx := errgroup.WithContext(ctx)

	g.Go(func() error {
		_, err := m.RuffCheck(ctx, source)
		return err
	})

	g.Go(func() error {
		_, err := m.RuffFormat(ctx, source)
		return err
	})

	g.Go(func() error {
		_, err := m.TypeCheck(ctx, source)
		return err
	})

	g.Go(func() error {
		_, err := m.FrontendCheck(ctx, source)
		return err
	})

	g.Go(func() error {
		_, err := m.FrontendLint(ctx, source)
		return err
	})

	if err := g.Wait(); err != nil {
		return "", fmt.Errorf("checks failed: %w", err)
	}

	return "All checks passed", nil
}
