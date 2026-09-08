#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"
REF="${2:?reference013}"
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
not_grep(){ local n="$1" p="$2" f="$3"; if grep -Fq "$p" "$f"; then bad "$n"; else ok "$n"; fi; }

check claude_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$CLAUDE"
check chatgpt_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check origin_policy_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
check web_bridge_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
grep_ok identity_014 'nexus_provider_profile_c002_claude_oauthhandoff014' "$MAIN"
grep_ok popup_same_profile 'WebViewCompat.setProfile(popup, PROFILE_NAME)' "$MAIN"
grep_ok popup_origin_policy 'OriginPolicy.isTopLevelNavigationAllowed(rawUrl)' "$MAIN"
grep_ok exact_google_host 'host == "accounts.google.com"' "$MAIN"
grep_ok exact_youtube_host 'host == "accounts.youtube.com"' "$MAIN"
grep_ok exact_google_fr_host 'host == "accounts.google.fr"' "$MAIN"
grep_ok provider_close_no_reload 'closeAuthPopup("provider_window_close")' "$MAIN"
grep_ok provider_close_starts_handoff 'beginOAuthHandoffObservation("provider_window_close")' "$MAIN"
grep_ok oauth_return_starts_handoff 'beginOAuthHandoffObservation("oauth_returned_claude")' "$MAIN"
not_grep no_013_immediate_reload_constant 'AUTH_POPUP_MAIN_RELOAD_DELAY_MS' "$MAIN"
not_grep no_reloadMain_parameter 'reloadMain' "$MAIN"
grep_ok popup_destroy_grace 'AUTH_POPUP_DESTROY_GRACE_MS = 750L' "$MAIN"
grep_ok passive_wait_bounded 'OAUTH_HANDOFF_PASSIVE_WAIT_MS = 6_000L' "$MAIN"
grep_ok fallback_wait_bounded 'OAUTH_HANDOFF_FALLBACK_WAIT_MS = 8_000L' "$MAIN"
grep_ok single_fallback_flag 'oauthHandoffFallbackUsed' "$MAIN"
grep_ok fallback_reload_event 'OAUTH_HANDOFF_FALLBACK_RELOAD' "$MAIN"
grep_ok fallback_reload_present 'webView.reload()' "$MAIN"
grep_ok terminal_after_fallback 'CLAUDE_OAUTH_HANDOFF_NOT_ESTABLISHED' "$MAIN"
grep_ok transient_wait_status 'OAUTH_HANDOFF_WAIT_STATUS' "$MAIN"
grep_ok authenticated_handoff 'OAUTH_HANDOFF_AUTHENTICATED' "$MAIN"
grep_ok execution_handoff_guard 'CLAUDE_OAUTH_HANDOFF_PENDING_AT_EXECUTION' "$MAIN"
grep_ok auth_stability_preserved 'CLAUDE_AUTH_STABLE_MIN_MS = 1_500L' "$MAIN"
grep_ok describe_stability_preserved 'AUTH_STABILITY_PASS' "$MAIN"
grep_ok transport_preserved 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' "$MAIN"
grep_ok execution_still_enabled 'startExecutionProof(origin)' "$MAIN"
grep_ok nested_window_fail_closed 'ANDROID_AUTH_WINDOW_NESTED_WINDOW_BLOCKED' "$MAIN"
grep_ok unknown_origin_fail_closed 'ANDROID_AUTH_WINDOW_ORIGIN_BLOCKED' "$MAIN"

# Inspect closeAuthPopup specifically: no stopLoading and no parent reload are allowed in the normal provider-close helper.
check close_helper_graceful python3 - "$MAIN" <<'PY'
import sys
s=open(sys.argv[1]).read()
start=s.index('    private fun closeAuthPopup(reason: String) {')
end=s.index('\n    private fun disposeAuthPopup() {', start)
block=s[start:end]
assert 'popup.stopLoading()' not in block
assert 'webView.reload()' not in block
assert 'popup.destroy()' in block
assert 'AUTH_POPUP_DESTROY_GRACE_MS' in block
PY

# During handoff, non-authenticated states must return before descriptor/DESCRIBE construction.
check handoff_precedes_descriptor python3 - "$MAIN" <<'PY'
import sys
s=open(sys.argv[1]).read()
a=s.index('        if (oauthHandoffPending) {')
b=s.index('        val descriptor = BridgeDescriptor(', a)
segment=s[a:b]
assert 'return' in segment
assert 'authState == "AUTHENTICATED"' in segment
PY

echo "CLAUDE_OAUTH_HANDOFF_014_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
