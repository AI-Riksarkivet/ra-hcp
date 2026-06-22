# Claude Code Setup

Two buckets of skills:

- **Shared** language/toolchain + UI skills come from the **[`ra-skills`](https://github.com/AI-Riksarkivet/ra-skills)** marketplace — not vendored here (incl. `shadcn-svelte`). Edit them in ra-skills.
- **HCP-private** skills stay vendored in `.claude/skills/`: `hcp-backend`, `hcp-frontend`, `hcp-sdk`, `testing-python`. They document HCP/MAPI internals (kept out of the public marketplace). Edit them in place.

Full RA Claude surface: [ra-skills' README](https://github.com/AI-Riksarkivet/ra-skills#what-we-use--the-full-ra-claude-surface).

## Setup

```bash
make claude-bootstrap   # idempotent — re-run anytime
```

Driven from `.claude/settings.json` (the single source of truth): adds the declared marketplaces and installs the enabled plugins at project scope. The vendored HCP skills load automatically from `.claude/skills/` — no install step.

## Troubleshooting

- **Skill missing?** Run `make claude-bootstrap`, then check `claude plugin list`.
- **Drift?** `.claude/settings.json` is authoritative; `.claude/settings.local.json` is personal-only.
