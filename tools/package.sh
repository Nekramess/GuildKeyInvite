#!/usr/bin/env bash
# Build the release zip: <Addon>-v<Version>-forever.zip (internal name, version from the .toc).
# Usage: bash tools/package.sh [output-dir]   (default: repo root). Prints the zip path.
set -euo pipefail

ADDON="GuildKeyInvite"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOC="$ROOT/$ADDON/$ADDON.toc"

VERSION="$(sed -n 's/^## Version:[[:space:]]*//p' "$TOC" | tr -d '\r' | head -n1)"
if [ -z "$VERSION" ]; then
    echo "No '## Version:' line in $TOC" >&2
    exit 1
fi

OUT="${1:-$ROOT}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
ZIP="$OUT/$ADDON-v$VERSION-forever.zip"

rm -f "$ZIP"
(cd "$ROOT" && zip -qr "$ZIP" "$ADDON" -x '*.DS_Store')
echo "$ZIP"
