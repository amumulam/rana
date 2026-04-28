#!/bin/sh
set -e

TAG="${1:-$CI_COMMIT_TAG}"
OUTFILE="${2:-changelog.txt}"
PREV_TAG=$(git tag --list 'v*' --sort=-version:refname | grep -v "^${TAG}$" | head -1)

if [ -z "$PREV_TAG" ]; then
    echo "## ${TAG}" > "$OUTFILE"
    echo "" >> "$OUTFILE"
    echo "Initial release." >> "$OUTFILE"
else
    RANGE="${PREV_TAG}..${TAG}"
    {
        echo "## ${TAG}"
        echo ""
        echo "Changes since ${PREV_TAG}:"
        echo ""
        FEATS=$(git log "$RANGE" --oneline --grep='^feat' | sed 's/^/• /' || true)
        if [ -n "$FEATS" ]; then echo "### ✨ Features"; echo "$FEATS"; echo ""; fi
        FIXES=$(git log "$RANGE" --oneline --grep='^fix' | sed 's/^/• /' || true)
        if [ -n "$FIXES" ]; then echo "### 🐛 Fixes"; echo "$FIXES"; echo ""; fi
        REFACTORS=$(git log "$RANGE" --oneline --grep='^refactor' | sed 's/^/• /' || true)
        if [ -n "$REFACTORS" ]; then echo "### ♻️ Refactoring"; echo "$REFACTORS"; echo ""; fi
        DOCS=$(git log "$RANGE" --oneline --grep='^docs' | sed 's/^/• /' || true)
        if [ -n "$DOCS" ]; then echo "### 📝 Docs"; echo "$DOCS"; echo ""; fi
        OTHER=$(git log "$RANGE" --oneline --grep='^feat' --invert-grep --grep='^fix' --invert-grep --grep='^refactor' --invert-grep --grep='^docs' --invert-grep | sed 's/^/• /' || true)
        if [ -n "$OTHER" ]; then echo "### 📦 Other"; echo "$OTHER"; echo ""; fi
    } > "$OUTFILE"
fi

cat "$OUTFILE"