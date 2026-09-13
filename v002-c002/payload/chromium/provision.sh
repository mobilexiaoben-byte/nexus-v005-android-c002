#!/usr/bin/env bash
set -euo pipefail
REVISION="1696878"
URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/${REVISION}/chrome-linux.zip"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
curl -fL --retry 3 --retry-delay 2 "$URL" -o "$TMP/chromium.zip"
unzip -q "$TMP/chromium.zip" -d "$TMP/extract"
[[ -x "$TMP/extract/chrome-linux/chrome" ]]
rm -rf "$ROOT"/*
cp -a "$TMP/extract/chrome-linux/." "$ROOT/"
mv "$ROOT/chrome" "$ROOT/chromium"
chmod 0755 "$ROOT/chromium"
printf '%s\n' "$REVISION" > "$ROOT/REVISION"
sha256sum "$TMP/chromium.zip" | awk '{print $1}' > "$ROOT/SOURCE_ZIP_SHA256"
printf '%s\n' "$URL" > "$ROOT/SOURCE_URL"
"$ROOT/chromium" --version
