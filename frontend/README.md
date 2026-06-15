# HCP Frontend

SvelteKit 2 + Svelte 5 frontend for the HCP application, running on **Bun**.

## Tech Stack

- **Runtime:** Bun
- **Framework:** SvelteKit 2 + Svelte 5
- **Styling:** Tailwind CSS 4, tw-animate-css
- **Components:** Bits UI, Lucide Svelte icons
- **Forms:** SvelteKit Superforms + Zod validation
- **Theme:** Mode Watcher (light/dark toggle)
- **Animations:** GSAP

## Getting Started

### Install dependencies

```bash
bun install
```

### Start the dev server

```bash
bun run dev
```

Or via the root Makefile (also sets `BACKEND_URL`):

```bash
make frontend-dev
```

The dev server starts at `http://localhost:5173` and proxies API calls to the
backend at `http://localhost:8000`.

### Build for production

```bash
bun run build
```

### Preview the production build

```bash
bun run preview
```

### Run the production server

The build output (`build/index.js`, from `svelte-adapter-bun`) is the SSR server.
Start it with Bun (listens on port 3000 by default):

```bash
bun run start
```

## Available Scripts

Run with `bun run <script>`.

| Script            | Command                                | Description                       |
| ----------------- | -------------------------------------- | --------------------------------- |
| `dev`             | `vite dev`                             | Start Vite dev server             |
| `build`           | `vite build`                           | Build for production              |
| `preview`         | `vite preview`                         | Preview production build          |
| `start`           | `bun ./build/index.js`                 | Run the production SSR server     |
| `sync`            | `svelte-kit sync`                      | SvelteKit sync (codegen)          |
| `check`           | `svelte-kit sync && svelte-check ...`  | TypeScript type checking          |
| `format`          | `prettier --write .`                   | Format code (Prettier)            |
| `format:check`    | `prettier --check .`                   | Check formatting without writing  |
| `storybook`       | `storybook dev -p 6006`                | Start Storybook dev server        |
| `build-storybook` | `storybook build`                      | Build Storybook static site       |

## Project Structure

```
frontend/
├── src/
│   ├── routes/
│   │   ├── login/              # Authentication
│   │   ├── (app)/              # Protected routes
│   │   │   ├── dashboard/      # Main dashboard
│   │   │   ├── tenants/        # Tenant management
│   │   │   ├── buckets/        # S3 bucket browser
│   │   │   └── users/          # User management
│   │   └── api/[...path]/      # API proxy
│   └── lib/
│       ├── components/         # Shared components
│       └── hooks/              # Svelte hooks
├── package.json                # Scripts and dependencies (Bun)
├── svelte.config.js            # Svelte compiler config
├── vite.config.ts              # Vite bundler config
└── tsconfig.json               # TypeScript config
```
