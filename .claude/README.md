# Claude Code Setup

Skills are split into two buckets:

- **Shared skills come from the [`ra-skills`](https://github.com/AI-Riksarkivet/ra-skills) marketplace** — the single source of truth for RA's language/toolchain skills (`dagger`, `fastapi`, `otel`, `python-infrastructure`, `writing-python`, `zensical-setup`, `zensical-authoring`, …). They are **not** vendored under `.claude/skills/` anymore; this kills the per-repo copy-drift. To change one, edit it in ra-skills.
- **HCP-private skills stay vendored** in `.claude/skills/` — `hcp-backend`, `hcp-frontend`, `hcp-sdk`, `shadcn-svelte-skill`, and ra-hcp's own `testing-python`. These document HCP/MAPI internals and are specific to this repo, so they live here, not in the public ra-skills marketplace.

The full RA Claude surface (shared skills + third-party marketplaces + MCP servers) is documented canonically in **[ra-skills' README](https://github.com/AI-Riksarkivet/ra-skills#what-we-use--the-full-ra-claude-surface)**.

## Bootstrap (fresh checkout)

```bash
make claude-bootstrap
```

Idempotent — adds every marketplace in `.claude/settings.json` → `extraKnownMarketplaces` and installs every plugin in `enabledPlugins` (project scope). `.claude/settings.json` is the **single source of truth**; the bootstrap is driven from it, so a fresh checkout reproduces the active surface. The vendored HCP skills load automatically from `.claude/skills/` — no install step.

## The active surface

| Kind | What | Where |
|---|---|---|
| **Shared skills** | `*@ra-skills` (dagger, fastapi, otel, python-infrastructure, writing-python, zensical-setup, zensical-authoring) | `enabledPlugins` + `extraKnownMarketplaces.ra-skills` |
| **HCP-private skills** | `hcp-backend`, `hcp-frontend`, `hcp-sdk`, `shadcn-svelte-skill`, `testing-python` | vendored in `.claude/skills/` |
| **3rd-party plugins** | `toolkit-skills` / `mcp-essentials` / `analytics` (claude-code-toolkit), `astral`, `svelte-skills`, `redis-development` (claude-plugins-official) | `enabledPlugins` + `extraKnownMarketplaces` |

> Dropped during unification: the dangling `svelte@svelte` and `svelte-flow@linehaulai-claude-marketplace` enables; `redis-development` re-pointed from a missing `redis` marketplace to the installed `claude-plugins-official`.

## Editing skills

- **Shared skill** → edit it in [`ra-skills`](https://github.com/AI-Riksarkivet/ra-skills), then `make claude-bootstrap` (or `claude plugin update <name>@ra-skills`) here.
- **HCP-private skill** → edit it directly under `.claude/skills/<name>/`. Keep the frontmatter `name` equal to the directory basename.

## Layout

```
.claude/
├── README.md              # this file
├── settings.json          # committed: enabledPlugins + extraKnownMarketplaces (single source of truth)
├── settings.local.json    # personal overrides (gitignored)
├── commands/              # project-local slash commands
├── hooks/                 # project-local lifecycle hooks
└── skills/                # HCP-PRIVATE skills only (hcp-*, shadcn-svelte-skill, testing-python)
```
