package main

import (
	"dagger/hcp-app/internal/dagger"
)

// BuildBackend builds the backend container from .docker/backend.dockerfile.
func (m *HcpApp) BuildBackend(source *dagger.Directory) *dagger.Container {
	return source.
		DockerBuild(dagger.DirectoryDockerBuildOpts{
			Dockerfile: ".docker/backend.dockerfile",
		})
}

// BuildFrontend builds the frontend container from .docker/frontend.dockerfile.
func (m *HcpApp) BuildFrontend(source *dagger.Directory) *dagger.Container {
	return source.
		DockerBuild(dagger.DirectoryDockerBuildOpts{
			Dockerfile: ".docker/frontend.dockerfile",
		})
}
