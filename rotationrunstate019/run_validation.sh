#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root019}"
REF="${2:?reference018}"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
PROV="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
CHATGPT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
ORIGIN="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
GRADLE="$ROOT/app/build.gradle.kts"
MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"
pass=0; fail=0
ok(){ echo "PASS $1"; pass=$((pass+1)); }
bad(){ echo "FAIL $1"; fail=$((fail+1)); }
check(){ local n="$1"; shift; if "$@"; then ok "$n"; else bad "$n"; fi; }
grep_ok(){ local n="$1" p="$2" f="$3"; grep -Fq "$p" "$f" && ok "$n" || bad "$n"; }

check claude_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$PROV"
check chatgpt_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check origin_policy_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
check web_bridge_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
grep_ok application_id_019 'applicationId = "nexus.android.c002.rotationrunstate019"' "$GRADLE"
grep_ok version_019 'versionName = "0.0.20-c002-rotation-runstate019"' "$GRADLE"
grep_ok label_019 'android:label="NEXUS C002 ROTATION RUNSTATE SAFE 019"' "$MANIFEST"
grep_ok rotation_config_changes 'android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden"' "$MANIFEST"
grep_ok config_import 'import android.content.res.Configuration' "$MAIN"
grep_ok shared_prefs_import 'import android.content.SharedPreferences' "$MAIN"
grep_ok on_configuration_changed 'override fun onConfigurationChanged(newConfig: Configuration)' "$MAIN"
grep_ok webview_preserved_diag 'webview_preserved=true' "$MAIN"
grep_ok no_reload_in_config 'CONFIGURATION_CHANGED' "$MAIN"
grep_ok run_latch_prefs 'RUN_LATCH_PREFS = "nexus_v005_rotation_runstate_019"' "$MAIN"
grep_ok run_latch_inflight 'RUN_STATE_IN_FLIGHT = "IN_FLIGHT"' "$MAIN"
grep_ok run_latch_ttl 'RUN_LATCH_TTL_MS = 300_000L' "$MAIN"
grep_ok recreation_fail_closed 'ANDROID_INFLIGHT_RUN_RECREATION_DETECTED' "$MAIN"
grep_ok recreation_recent_gate 'priorAge in 0..RUN_LATCH_TTL_MS' "$MAIN"
grep_ok latch_arm_function 'private fun armRunLatch()' "$MAIN"
grep_ok latch_close_function 'private fun closeRunLatch(state: String)' "$MAIN"
grep_ok latch_armed_before_post 'armRunLatch()' "$MAIN"
grep_ok terminal_pass_closes 'closeRunLatch(RUN_STATE_TERMINAL_PASS)' "$MAIN"
grep_ok terminal_block_closes 'closeRunLatch(RUN_STATE_TERMINAL_BLOCKED)' "$MAIN"
grep_ok no_payload_persisted 'RUN_LATCH_STARTED_AT_KEY = "started_at_ms"' "$MAIN"
grep_ok provider_contract_preserved 'NEXUS_PROVIDER_COMPOSER_STATE_SYNC_018_OK' "$MAIN"
grep_ok provider_ui_actuation_preserved 'PROVIDER_UI_ACTUATE' "$MAIN"
grep_ok generation_gate_preserved 'CLAUDE_GENERATION_OBSERVED__' "$PROV"

if python3 - "$MAIN" <<'PY'
import sys
s=open(sys.argv[1]).read()
a=s.index('override fun onConfigurationChanged(newConfig: Configuration)')
b=s.index('private fun configureAuthPopup',a)
block=s[a:b]
assert 'loadUrl(' not in block
assert '.reload(' not in block
assert 'WebView(' not in block
PY
then ok configuration_handler_no_provider_reload; else bad configuration_handler_no_provider_reload; fi

if python3 - "$MAIN" <<'PY'
import sys
s=open(sys.argv[1]).read()
a=s.index('private fun armRunLatch()')
b=s.index('private fun handleProviderAck',a)
block=s[a:b]
for forbidden in ['question','prompt','frozenPackage','resultPack','cookie','token','provider_meta']:
    assert forbidden not in block, forbidden
PY
then ok run_latch_metadata_only; else bad run_latch_metadata_only; fi

echo "ROTATION_RUNSTATE_SAFE_019_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
