#!/bin/sh
set -e

TAG="$1"
CHANGELOG_FILE="$2"
OUTPUT="$3"

if [ -f "RELEASE_NOTE.md" ]; then
    echo "Using RELEASE_NOTE.md as release description"
    jq -n --arg tag "$TAG" --arg name "rana $TAG" --rawfile desc "RELEASE_NOTE.md" \
        '{"tag_name":$tag,"name":$name,"description":$desc}' \
        > "$OUTPUT"
else
    echo "RELEASE_NOTE.md not found, using changelog.txt as fallback"
    jq -n --arg tag "$TAG" --arg name "rana $TAG" --rawfile desc "$CHANGELOG_FILE" \
        '{"tag_name":$tag,"name":$name,"description":$desc}' \
        > "$OUTPUT"
fi