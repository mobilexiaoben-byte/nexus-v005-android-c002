#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
LAYOUT="$ROOT/app/src/main/res/layout/activity_main.xml"
MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"
PASS=0
FAIL=0
check() {
  local id="$1"; shift
  if "$@"; then echo "PASS $id"; PASS=$((PASS+1)); else echo "FAIL $id"; FAIL=$((FAIL+1)); fi
}
check_text() { grep -Fq "$2" "$1"; }

check D01_marker check_text "$MAIN" 'V005-C002-AUTHFLOWDIAG003-DEVICE-001'
check D02_page_started check_text "$MAIN" 'override fun onPageStarted'
check D03_page_finished check_text "$MAIN" 'override fun onPageFinished'
check D04_override_loading check_text "$MAIN" 'override fun shouldOverrideUrlLoading'
check D05_received_error check_text "$MAIN" 'override fun onReceivedError'
check D06_http_error check_text "$MAIN" 'override fun onReceivedHttpError'
check D07_main_frame check_text "$MAIN" 'request.isForMainFrame'
check D08_new_window check_text "$MAIN" 'override fun onCreateWindow'
check D09_popup_fail_closed check_text "$MAIN" 'AUTHFLOW_NEW_WINDOW_REQUESTED'
check D10_sanitized_url check_text "$MAIN" 'sanitizeUrl(rawUrl)'
check D11_no_query_fragment_logging bash -c "! grep -Eq 'uri\.(query|encodedQuery|fragment|encodedFragment)|request\.url\.query|request\.url\.fragment' '$MAIN'"
check D12_no_raw_loading_status bash -c "! grep -Fq 'loading \$url' '$MAIN'"
check D13_origin_policy_unchanged bash -c "cd '$ROOT' && echo '3540ddf94bf7e1693711140e8b43313c63989a021e795beaeef116acea8c03ce  app/src/main/java/nexus/android/c002/web/OriginPolicy.kt' | sha256sum -c - >/dev/null"
check D14_bridge_unchanged bash -c "cd '$ROOT' && echo 'a842eb5d15d23b0ace09674585cefbfba2a753c155eeb5b0c0df6aaf9324275a  app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt' | sha256sum -c - >/dev/null"
check D15_chatgpt_adapter_unchanged bash -c "cd '$ROOT' && echo '4a183b76dfb56eb9d2f51a553e69ad138a9dea1d251c221c5b6f09e6dbe618ea  app/src/main/assets/nexus/chatgpt_provider_c002.js' | sha256sum -c - >/dev/null"
check D16_claude_adapter_unchanged bash -c "cd '$ROOT' && echo 'f1dc78cdbadcc252a529c2db86b15ac42a92f0f2c132181cd1072bc24b131366  app/src/main/assets/nexus/claude_provider_c002.js' | sha256sum -c - >/dev/null"
check D17_no_provider_job check_text "$MAIN" 'Deliberately no provider job dispatch here.'
check D18_side_by_side_package check_text "$ROOT/app/build.gradle.kts" 'applicationId = "nexus.android.c002.authflowdiag003"'
check D19_version_code check_text "$ROOT/app/build.gradle.kts" 'versionCode = 4'
check D20_debugging_disabled check_text "$MAIN" 'WebView.setWebContentsDebuggingEnabled(false)'
check D21_no_allowlist_edit bash -c "cd '$ROOT' && sha256sum -c AUTHFLOWDIAG003_BASELINE_SHA256.txt >/dev/null"
check D22_consecutive_dedup check_text "$MAIN" 'previous?.fingerprint == fingerprint'
check D23_repeat_counter check_text "$MAIN" 'previous.repeatCount += 1'
check D24_duplicate_no_render bash -c "python3 - '$MAIN' <<'PY'
import sys
s=open(sys.argv[1]).read()
needle='previous.repeatCount += 1\\n            return'
raise SystemExit(0 if needle in s else 1)
PY"
check D25_auth_transition_only check_text "$MAIN" 'val authChanged = authState != lastAuthState'
check D26_compact_two_lines check_text "$MAIN" 'const val COMPACT_STATUS_LINES = 2'
check D27_expanded_bounded check_text "$MAIN" 'const val EXPANDED_STATUS_LINES = 8'
check D28_layout_bounded check_text "$LAYOUT" 'android:maxLines="2"'
check D29_layout_ellipsize check_text "$LAYOUT" 'android:ellipsize="end"'
check D30_tap_expand check_text "$MAIN" 'diagnosticExpanded = !diagnosticExpanded'
check D31_auth_required_no_body bash -c "python3 - '$MAIN' <<'PY'
import sys
s=open(sys.argv[1]).read()
needle='currentHeadline = AUTH_REQUIRED_HEADLINE\\n                    currentBody = null'
raise SystemExit(0 if needle in s else 1)
PY"
check D32_webview_weight check_text "$LAYOUT" 'android:layout_weight="1"'
check D33_distinct_label check_text "$MANIFEST" 'android:label="NEXUS C002 AUTHFLOWDIAG003"'
check D34_profile_isolated check_text "$MAIN" 'nexus_provider_profile_c002_authflowdiag003'

printf 'AUTHFLOWDIAG003_STATIC_RESULT pass=%d fail=%d\n' "$PASS" "$FAIL"
test "$FAIL" -eq 0
