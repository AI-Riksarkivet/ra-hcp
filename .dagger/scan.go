package main

import (
	"context"
	"fmt"

	"dagger/ra-hcp/internal/dagger"
)

// scanFormat is Trivy's human-readable table output.
//
// The functions below default to severity "HIGH,CRITICAL" and exit-code 0:
// the scan is informational by default and always prints the full
// vulnerability table so you can see *what* is flagged. CI gates a release by
// passing --exit-code=1, which makes Trivy fail the pipeline when any matching
// CVE is present.
const scanFormat = "table"

// ScanBackend builds the backend image and scans it for known CVEs with Trivy.
func (m *RaHcp) ScanBackend(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// Comma-separated severities to report (UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
	// +default="HIGH,CRITICAL"
	// +optional
	severity string,
	// Trivy exit code on findings — 0 reports only, 1 fails the build
	// +default=0
	// +optional
	exitCode int,
) (string, error) {
	return dag.Trivy().ScanContainer(ctx, m.BuildBackend(source), dagger.TrivyScanContainerOpts{
		Severity: severity,
		ExitCode: exitCode,
		Format:   scanFormat,
	})
}

// ScanFrontend builds the frontend image and scans it for known CVEs with Trivy.
func (m *RaHcp) ScanFrontend(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// Comma-separated severities to report (UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
	// +default="HIGH,CRITICAL"
	// +optional
	severity string,
	// Trivy exit code on findings — 0 reports only, 1 fails the build
	// +default=0
	// +optional
	exitCode int,
) (string, error) {
	return dag.Trivy().ScanContainer(ctx, m.BuildFrontend(source), dagger.TrivyScanContainerOpts{
		Severity: severity,
		ExitCode: exitCode,
		Format:   scanFormat,
	})
}

// Scan builds both images and runs Trivy CVE scans over each. Reports are
// concatenated so a single call shows the full backend + frontend picture.
// Pass --exit-code=1 to gate a release on HIGH/CRITICAL findings.
func (m *RaHcp) Scan(
	ctx context.Context,
	// +defaultPath="/"
	source *dagger.Directory,
	// Comma-separated severities to report (UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
	// +default="HIGH,CRITICAL"
	// +optional
	severity string,
	// Trivy exit code on findings — 0 reports only, 1 fails the build
	// +default=0
	// +optional
	exitCode int,
) (string, error) {
	backend, err := m.ScanBackend(ctx, source, severity, exitCode)
	if err != nil {
		return "", fmt.Errorf("backend scan failed: %w", err)
	}

	frontend, err := m.ScanFrontend(ctx, source, severity, exitCode)
	if err != nil {
		return "", fmt.Errorf("frontend scan failed: %w", err)
	}

	return fmt.Sprintf(
		"=== backend (riksarkivet/ra-hcp) ===\n%s\n\n=== frontend (riksarkivet/ra-hcp-frontend) ===\n%s",
		backend, frontend,
	), nil
}

// ScanImage scans an already-published image ref (e.g. a Harbor/Docker Hub
// tag) for known CVEs with Trivy — for verifying what is actually live.
func (m *RaHcp) ScanImage(
	ctx context.Context,
	// Image ref to scan, e.g. "riksarkivet/ra-hcp:v0.2.0"
	imageRef string,
	// Comma-separated severities to report (UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL)
	// +default="HIGH,CRITICAL"
	// +optional
	severity string,
	// Trivy exit code on findings — 0 reports only, 1 fails the build
	// +default=0
	// +optional
	exitCode int,
) (string, error) {
	return dag.Trivy().ScanImage(ctx, imageRef, dagger.TrivyScanImageOpts{
		Severity: severity,
		ExitCode: exitCode,
		Format:   scanFormat,
	})
}
