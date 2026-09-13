#!/usr/bin/env bash
set -euo pipefail
APP_ID="nexus-desktop"
APP_NAME="NEXUS Desktop"
DEFAULT_PREFIX="${HOME}/.local/share/${APP_ID}"
PREFIX="${NEXUS_PREFIX:-$DEFAULT_PREFIX}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="${SOURCE_DIR}/payload"
fail(){ printf 'V002_BOOTSTRAP_FAIL:%s\n' "$1" >&2; exit 20; }
pass(){ printf 'V002_BOOTSTRAP_PASS:%s\n' "$1"; }
validate_payload(){
  [[ -x "${PAYLOAD}/chromium/chromium" ]] || fail "CHROMIUM_MISSING"
  [[ -f "${PAYLOAD}/bridge/manifest.json" ]] || fail "BRIDGE_MANIFEST_MISSING"
  [[ -f "${PAYLOAD}/bridge/background.js" ]] || fail "BRIDGE_BACKGROUND_MISSING"
  [[ -f "${PAYLOAD}/nexus/index.html" ]] || fail "NEXUS_ENTRY_MISSING"
  grep -q '"version": "0.1.6.4"' "${PAYLOAD}/bridge/manifest.json" || fail "BRIDGE_VERSION_MISMATCH"
  grep -q 'NEXUS_CLIENT_APP_BRIDGE_V0.1' "${PAYLOAD}/bridge/background.js" || fail "BRIDGE_CONTRACT_MISSING"
}
if [[ "${1:-}" == "--check" ]]; then validate_payload; pass "REAL_PAYLOAD_VALID"; exit 0; fi
validate_payload

tmp="${PREFIX}.installing.$$"
rm -rf "$tmp"
mkdir -p "$tmp"/{app,bridge,chromium,profile,config,logs}
cp -a "${PAYLOAD}/nexus/." "$tmp/app/"
cp -a "${PAYLOAD}/bridge/." "$tmp/bridge/"
cp -a "${PAYLOAD}/chromium/." "$tmp/chromium/"
cat > "$tmp/config/runtime.env" <<'EOF'
NEXUS_ENTRY_REL=app/index.html
NEXUS_PROFILE_REL=profile
NEXUS_BRIDGE_REL=bridge
NEXUS_CHROMIUM_REL=chromium/chromium
EOF
cat > "$tmp/nexus-desktop" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$BASE/config/runtime.env"
CHROMIUM="$BASE/$NEXUS_CHROMIUM_REL"
PROFILE="$BASE/$NEXUS_PROFILE_REL"
BRIDGE="$BASE/$NEXUS_BRIDGE_REL"
ENTRY="file://$BASE/$NEXUS_ENTRY_REL"
[[ -x "$CHROMIUM" ]] || { echo "NEXUS_LAUNCH_FAIL:CHROMIUM_MISSING" >&2; exit 30; }
[[ -f "$BRIDGE/manifest.json" ]] || { echo "NEXUS_LAUNCH_FAIL:BRIDGE_MISSING" >&2; exit 31; }
mkdir -p "$PROFILE" "$BASE/logs"
exec "$CHROMIUM" --user-data-dir="$PROFILE" --no-first-run --no-default-browser-check --disable-sync --disable-background-networking --disable-extensions-except="$BRIDGE" --load-extension="$BRIDGE" "$ENTRY"
EOF
chmod 0755 "$tmp/nexus-desktop"
mkdir -p "$BIN_DIR" "$DESKTOP_DIR"
if [[ -e "$PREFIX" ]]; then rm -rf "${PREFIX}.previous"; mv "$PREFIX" "${PREFIX}.previous"; fi
mv "$tmp" "$PREFIX"
ln -sfn "$PREFIX/nexus-desktop" "$BIN_DIR/nexus-desktop"
cat > "$DESKTOP_DIR/nexus-desktop.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_NAME}
Exec=${BIN_DIR}/nexus-desktop
Terminal=false
Categories=Utility;
EOF
pass "INSTALLED:${PREFIX}"
pass "ISOLATED_PROFILE:${PREFIX}/profile"
pass "AUTOMATED_BRIDGE:${PREFIX}/bridge"
