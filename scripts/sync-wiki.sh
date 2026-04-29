#!/bin/bash
set -euo pipefail

WIKI_DIR="${1:-wiki}"
BRANCH="master"
TMP_DIR=$(mktemp -d)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WIKI_SRC="$PROJECT_DIR/$WIKI_DIR"
WIKI_DST="$TMP_DIR/wikirepo"

if [ -z "${WIKI_REPO_URL:-}" ]; then
    echo "Error: WIKI_REPO_URL not set"
    exit 1
fi

git clone --depth 1 "$WIKI_REPO_URL" "$WIKI_DST" 2>/dev/null || {
    mkdir -p "$WIKI_DST"
    git init "$WIKI_DST"
    cd "$WIKI_DST" && git checkout -b "$BRANCH" 2>/dev/null || git branch -m "$BRANCH"
}

rsync -a --exclude='.git' --delete "$WIKI_SRC/" "$WIKI_DST/"

cd "$WIKI_DST"
git add -A
if git diff --cached --quiet; then
    echo "No changes to sync."
else
    git commit -m "sync wiki from repo ${CI_COMMIT_SHORT_SHA:-manual}"
    git push origin "$BRANCH"
fi

cd "$PROJECT_DIR"
rm -rf "$TMP_DIR"
echo "Done."
