#!/bin/sh
set -e

TAG="${1:-$CI_COMMIT_TAG}"
PREV_TAG=$(git tag --list 'v*' --sort=-version:refname | grep -v "^${TAG}$" | head -1)

if [ -z "$PREV_TAG" ]; then
    RANGE=""
    HEADER="## ${TAG}\n\nInitial release."
else
    RANGE="${PREV_TAG}..${TAG}"
    FEATS=$(git log "$RANGE" --oneline --grep='^feat' | sed 's/^/• /' || true)
    FIXES=$(git log "$RANGE" --oneline --grep='^fix' | sed 's/^/• /' || true)
    REFACTORS=$(git log "$RANGE" --oneline --grep='^refactor' | sed 's/^/• /' || true)
    DOCS=$(git log "$RANGE" --oneline --grep='^docs' | sed 's/^/• /' || true)
    OTHER=$(git log "$RANGE" --oneline --grep='^feat' --invert-grep --grep='^fix' --invert-grep --grep='^refactor' --invert-grep --grep='^docs' --invert-grep | sed 's/^/• /' || true)

    HEADER="## ${TAG}\n\nChanges since ${PREV_TAG}:\n"
    if [ -n "$FEATS" ]; then HEADER="${HEADER}\n### ✨ Features\n${FEATS}\n"; fi
    if [ -n "$FIXES" ]; then HEADER="${HEADER}\n### 🐛 Fixes\n${FIXES}\n"; fi
    if [ -n "$REFACTORS" ]; then HEADER="${HEADER}\n### ♻️ Refactoring\n${REFACTORS}\n"; fi
    if [ -n "$DOCS" ]; then HEADER="${HEADER}\n### 📝 Docs\n${DOCS}\n"; fi
    if [ -n "$OTHER" ]; then HEADER="${HEADER}\n### 📦 Other\n${OTHER}\n"; fi
fi

printf "$HEADER"