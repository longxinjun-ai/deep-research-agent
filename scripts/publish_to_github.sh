#!/usr/bin/env bash
# One-shot publish: creates the GitHub repo (if missing) and pushes.
# Prerequisite (once):  gh auth login
set -euo pipefail
cd "$(dirname "$0")/.."

if ! gh auth status >/dev/null 2>&1; then
  echo "Not authenticated. Run:  gh auth login   (choose GitHub.com > HTTPS > browser)"
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main
else
  # public by default; pass --private to keep it private
  gh repo create deep-research-agent --public --source=. --remote=origin --push \
    --description "Document-driven deep & wide research agent system — synthesis of grapeot's deep_research_agent + codex_wide_research + context-infrastructure"
fi
echo "Done. Repo URL:"
gh repo view --json url -q .url
