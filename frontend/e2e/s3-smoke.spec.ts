import { test, expect } from '@playwright/test';

// Full-stack smoke test: browser → SvelteKit SSR + remote functions → FastAPI
// backend → real S3 (MinIO). This is the only test that exercises the entire
// chain end to end; if auth wiring, the remote-function layer, the backend S3
// adapter, or the storage config breaks, this fails. Run via `dagger call e2e`
// (or `make e2e`), which provides the running stack on E2E_BASE_URL.

const USERNAME = process.env.E2E_USERNAME ?? 'minioadmin';
const PASSWORD = process.env.E2E_PASSWORD ?? 'minioadmin123';

test('login, create a bucket, and see it listed', async ({ page }) => {
	// 1. Log in. The backend always issues a JWT (credentials are validated by
	//    S3/MinIO on the actual calls, not at login time).
	await page.goto('/login');
	await page.locator('#username').fill(USERNAME);
	await page.locator('#password').fill(PASSWORD);
	await page.getByRole('button', { name: 'Sign in' }).click();

	// Login redirects to /namespaces (a MAPI page). In this S3-only stack we go
	// straight to the buckets page, which is always mounted.
	await page.waitForURL(/\/(namespaces|buckets)/);
	await page.goto('/buckets');
	await expect(page.getByRole('button', { name: 'Create Bucket' })).toBeVisible();

	// 2. Create a uniquely-named bucket through the UI.
	const bucket = `e2e-smoke-${Date.now()}`;
	await page.getByRole('button', { name: 'Create Bucket' }).click();
	await page.locator('#bucket-name').fill(bucket);
	await page.getByRole('button', { name: 'Create', exact: true }).click();

	// The dialog closes only on a successful create (errors keep it open).
	await expect(page.locator('#bucket-name')).toBeHidden({ timeout: 15000 });

	// 3. The bucket must appear in the list LIVE — no manual refresh. This guards
	//    the mutation→query refresh wiring (regression: stale list after create).
	await expect(page.getByText(bucket)).toBeVisible({ timeout: 15000 });

	// 4. Open the bucket and create a folder. It must appear LIVE (object-list
	//    refresh) AND remain visible when searched (folder-search regression:
	//    search must not strip folders by forcing flat mode).
	await page.goto(`/buckets/${bucket}`);
	await page.getByRole('button', { name: 'New Folder' }).click();
	const folder = `e2e-folder-${Date.now()}`;
	await page.locator('#folder-name').fill(folder);
	await page.getByRole('button', { name: 'Create', exact: true }).click();
	await expect(page.getByText(folder)).toBeVisible({ timeout: 15000 });

	await page.getByPlaceholder(/Search by name prefix/i).fill(folder);
	await expect(page.getByText(folder)).toBeVisible({ timeout: 15000 });
});
