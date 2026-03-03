#!/usr/bin/env bash
# Auto-format files by type after Claude Code edits
set -euo pipefail

for f in "$@"; do
  [ -f "$f" ] || continue
  case "$f" in
    *.py)
      uvx ruff format "$f"
      uvx ruff check --fix "$f" || true
      ;;
    *.svelte)
      cd /home/coder/hcp/frontend
      npx prettier --plugin prettier-plugin-svelte --write "$f"
      ;;
    *.ts|*.js)
      ~/.deno/bin/deno fmt "$f"
      ;;
  esac
done
