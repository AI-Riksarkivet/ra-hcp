package main

import (
	"context"

	"dagger/ra-hcp/internal/dagger"
)

// sdkBuilder returns a uv container with the workspace mounted and the sibling
// packages/*/src/rahcp_* modules copied into src/, so a plain `uv build`
// produces one self-contained rahcp wheel (see the sources=["src"] config in
// pyproject.toml). The copy is what makes `pip install rahcp` ship everything
// without any rahcp-* names on PyPI.
func (m *RaHcp) sdkBuilder(source *dagger.Directory) *dagger.Container {
	return dag.Container().From(uvPythonImage).
		WithMountedCache("/root/.cache/uv", dag.CacheVolume("uv-cache")).
		WithDirectory("/workspace", source).
		WithWorkdir("/workspace").
		WithExec([]string{"sh", "-c", "cp -r packages/rahcp-*/src/rahcp_* src/"})
}

// BuildSdk builds the single self-contained `rahcp` wheel + source distribution.
// The backend is a separate project and is never built. Returns the dist/
// directory (`dagger call build-sdk --source=. export --path=dist`).
func (m *RaHcp) BuildSdk(
	// +defaultPath="/"
	source *dagger.Directory,
) *dagger.Directory {
	return m.sdkBuilder(source).
		WithExec([]string{"uv", "build", "--out-dir", "/workspace/dist"}).
		Directory("/workspace/dist")
}

// PublishSdk builds and uploads the rahcp package to a Python index (PyPI by
// default). The token is passed to uv via UV_PUBLISH_TOKEN, so it never appears
// on the command line. --check-url makes the run idempotent: a version already
// on the index is skipped, so re-running a release is safe.
func (m *RaHcp) PublishSdk(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// Index API token (PyPI: https://pypi.org/manage/account/token/). Passed to
	// uv as UV_PUBLISH_TOKEN.
	token *dagger.Secret,
	// Upload endpoint. Override with the TestPyPI URL to rehearse a release.
	// +default="https://upload.pypi.org/legacy/"
	// +optional
	publishURL string,
	// Simple-index URL used to skip files that already exist on the index.
	// +default="https://pypi.org/simple/"
	// +optional
	checkURL string,
) (string, error) {
	return m.sdkBuilder(source).
		WithSecretVariable("UV_PUBLISH_TOKEN", token).
		WithExec([]string{"uv", "build", "--out-dir", "/workspace/dist"}).
		WithExec([]string{
			"uv", "publish",
			"--publish-url", publishURL,
			"--check-url", checkURL,
			"/workspace/dist/*",
		}).
		Stdout(ctx)
}
