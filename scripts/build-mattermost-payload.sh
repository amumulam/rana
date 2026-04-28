#!/bin/sh
set -e

TAG="$1"
CHANGELOG_FILE="$2"
URL="$3"
OUTPUT="$4"

DESC=$(jq -Rs . "$CHANGELOG_FILE")
jq -n --arg tag "$TAG" --arg url "$URL" --argjson desc "$DESC" \
    '{"text":("rana " + $tag + " released!\n\n" + $desc + "\n\nRelease: " + $url)}' \
    > "$OUTPUT"