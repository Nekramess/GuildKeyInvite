#!/usr/bin/env bash
# Rebuild the zip with tools/package.sh and keep exactly one zip in releases/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ZIP="$(bash "$ROOT/tools/package.sh" "$TMP")"
mkdir -p "$ROOT/releases"
rm -f "$ROOT"/releases/*.zip
cp "$ZIP" "$ROOT/releases/"
echo "releases/$(basename "$ZIP")"
