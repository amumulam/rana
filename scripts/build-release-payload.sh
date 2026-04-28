#!/bin/sh
set -e

TAG="$1"
CHANGELOG_FILE="$2"
OUTPUT="$3"

jq -n --arg tag "$TAG" --arg name "rana $TAG" --rawfile desc "$CHANGELOG_FILE" \
    '{"tag_name":$tag,"name":$name,"description":$desc}' \
    > "$OUTPUT"