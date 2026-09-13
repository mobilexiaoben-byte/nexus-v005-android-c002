#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ok(){ echo "PASS:$1"; }
[[ -x "$ROOT/payload/chromium/chromium" ]] || { echo FAIL:CHROMIUM_REAL_MISSING; exit 1; }; ok CHROMIUM_REAL_PRESENT
"$ROOT/payload/chromium/chromium" --version | grep -qi 'Chrom'; ok CHROMIUM_EXECUTES
[[ "$(cat "$ROOT/payload/chromium/REVISION")" == "1696878" ]]; ok CHROMIUM_REVISION_PINNED
[[ -s "$ROOT/payload/chromium/SOURCE_ZIP_SHA256" ]]; ok CHROMIUM_SOURCE_HASH_CAPTURED
[[ -f "$ROOT/payload/bridge/manifest.json" ]]; ok BRIDGE_REAL_PRESENT
grep -q '"version": "0.1.6.4"' "$ROOT/payload/bridge/manifest.json"; ok BRIDGE_V001_FROZEN_VERSION
grep -q 'NEXUS_CLIENT_APP_BRIDGE_V0.1' "$ROOT/payload/bridge/background.js"; ok BRIDGE_CONTRACT_PRESENT
[[ -s "$ROOT/payload/nexus/index.html" ]]; ok NEXUS_REAL_ENTRY_PRESENT
HOME="$TMP/home0" "$ROOT/install.sh" --check | grep -q REAL_PAYLOAD_VALID; ok PAYLOAD_CHECK
HOME="$TMP/home1" NEXUS_PREFIX="$TMP/home1/.local/share/nexus-desktop" "$ROOT/install.sh" > "$TMP/install.log"
PREFIX="$TMP/home1/.local/share/nexus-desktop"
[[ -x "$PREFIX/nexus-desktop" ]]; ok LAUNCHER_CREATED
[[ -d "$PREFIX/profile" ]]; ok ISOLATED_PROFILE_CREATED
[[ -f "$PREFIX/bridge/manifest.json" ]]; ok BRIDGE_INSTALLED
[[ -x "$PREFIX/chromium/chromium" ]]; ok CHROMIUM_INSTALLED
grep -q '^Terminal=false$' "$TMP/home1/.local/share/applications/nexus-desktop.desktop"; ok NO_TERMINAL_USER_FLOW
if grep -RniE 'OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-[A-Za-z0-9]' "$PREFIX" >/dev/null 2>&1; then echo FAIL:API_KEY_MATERIAL_FOUND; exit 1; fi; ok NO_API_KEY_MATERIAL
HOME="$TMP/home1" NEXUS_PREFIX="$PREFIX" "$ROOT/install.sh" >/dev/null
[[ -d "${PREFIX}.previous" ]]; ok REINSTALL_PRESERVES_PREVIOUS
echo RESULT:16/16_PASS
