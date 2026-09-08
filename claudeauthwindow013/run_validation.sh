#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"
REF="${2:?reference012}"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
CHATGPT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
ORIGIN="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
pass=0; fail=0
ok(){ echo "PASS $1"; pass=$((pass+1)); }
bad(){ echo "FAIL $1"; fail=$((fail+1)); }
check(){ local n="$1"; shift; if "$@"; then ok "$n"; else bad "$n"; fi; }
grep_ok(){ local n="$1" p="$2" f="$3"; grep -Fq "$p" "$f" && ok "$n" || bad "$n"; }

check claude_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$CLAUDE"
check chatgpt_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check origin_policy_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
check web_bridge_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
grep_ok identity_013 'nexus_provider_profile_c002_claude_authwindow013' "$MAIN"
grep_ok popup_same_profile 'WebViewCompat.setProfile(popup, PROFILE_NAME)' "$MAIN"
grep_ok single_auxiliary_window 'single_auxiliary_window=true' "$MAIN"
grep_ok webview_transport 'WebView.WebViewTransport' "$MAIN"
grep_ok send_to_target 'resultMsg.sendToTarget()' "$MAIN"
grep_ok popup_uses_origin_policy 'OriginPolicy.isTopLevelNavigationAllowed(rawUrl)' "$MAIN"
grep_ok exact_google_host 'host == "accounts.google.com"' "$MAIN"
grep_ok exact_youtube_host 'host == "accounts.youtube.com"' "$MAIN"
grep_ok exact_google_fr_host 'host == "accounts.google.fr"' "$MAIN"
grep_ok oauth_return_clause 'authPopupSawExternalAuthHost && isClaudeHost(host)' "$MAIN"
grep_ok oauth_return_close 'closeAuthPopup("oauth_returned_claude", reloadMain = true)' "$MAIN"
grep_ok main_reload_shared_profile 'detail = "shared_profile=true"' "$MAIN"
grep_ok nested_window_fail_closed 'ANDROID_AUTH_WINDOW_NESTED_WINDOW_BLOCKED' "$MAIN"
grep_ok unknown_origin_fail_closed 'ANDROID_AUTH_WINDOW_ORIGIN_BLOCKED' "$MAIN"
grep_ok execution_window_terminal 'if (executionStarted && !terminalReceived)' "$MAIN"
grep_ok no_describe_while_popup 'AUTH_STABILITY_WAIT_AUTH_WINDOW_CLOSE' "$MAIN"
grep_ok no_execution_while_popup 'ANDROID_AUTH_WINDOW_STILL_OPEN_AT_EXECUTION' "$MAIN"
grep_ok auth_stability_preserved 'CLAUDE_AUTH_STABLE_MIN_MS = 1_500L' "$MAIN"
grep_ok transport_preserved 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' "$MAIN"
grep_ok multiple_windows_support 'setSupportMultipleWindows(true)' "$MAIN"
grep_ok js_auto_windows_disabled 'javaScriptCanOpenWindowsAutomatically = false' "$MAIN"

echo "CLAUDE_AUTH_WINDOW_013_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
