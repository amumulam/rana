#!/bin/bash
set -euo pipefail

WIKI_DIR="${1:-wiki}"
WIKI_REPO_URL="${WIKI_REPO_URL:-git@gitlab.vmic.xyz:ued-ai-lab/rana.wiki.git}"
BRANCH="master"
TMP_DIR=$(mktemp -d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WIKI_SRC="$PROJECT_DIR/$WIKI_DIR"
WIKI_DST="$TMP_DIR/wikirepo"

if git clone --depth 1 "$WIKI_REPO_URL" "$WIKI_DST" 2>/dev/null; then
    true
else
    mkdir -p "$WIKI_DST"
    git init "$WIKI_DST"
    (cd "$WIKI_DST" && git checkout -b "$BRANCH" 2>/dev/null || git branch -m "$BRANCH")
fi

rsync -a --exclude='.git' --delete "$WIKI_SRC/" "$WIKI_DST/"

cd "$WIKI_DST"
git add -A
if git diff --cached --quiet; then
    echo "No changes to sync."
else
    git commit -m "sync wiki"
    git push origin "$BRANCH" --force
fi

cd "$PROJECT_DIR"
rm -rf "$TMP_DIR"
echo "Done."
