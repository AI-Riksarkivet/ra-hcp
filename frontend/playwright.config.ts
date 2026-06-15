import { defineConfig, devices } from '@playwright/test';

// Full-stack e2e config. The test runs against an already-running frontend
// (provided by the Dagger `e2e` function, which wires frontend → backend →
// S3/MinIO). Point it at a local stack with E2E_BASE_URL, e.g.
//   make full-serve   # in one shell (frontend on :5174)
//   E2E_BASE_URL=http://localhost:5174 bun run e2e
const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:3000';

export default defineConfig({
	testDir: './e2e',
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 1 : 0,
	reporter: process.env.CI ? 'line' : 'list',
	use: {
		baseURL,
		trace: 'on-first-retry',
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
