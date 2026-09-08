#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"
REF="${2:?reference}"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
CHATGPT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
ORIGIN="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
pass=0; fail=0
ok(){ echo "PASS $1"; pass=$((pass+1)); }
bad(){ echo "FAIL $1"; fail=$((fail+1)); }
check(){ local name="$1"; shift; if "$@"; then ok "$name"; else bad "$name"; fi; }
check_grep(){ local name="$1" pat="$2" file="$3"; if grep -Fq "$pat" "$file"; then ok "$name"; else bad "$name"; fi; }
check_not_grep(){ local name="$1" pat="$2" file="$3"; if grep -Fq "$pat" "$file"; then bad "$name"; else ok "$name"; fi; }

check "claude_provider_byte_identical" cmp -s "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$CLAUDE"
check "chatgpt_provider_byte_identical" cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check "origin_policy_byte_identical" cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
check "web_bridge_byte_identical" cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
check_grep "identity_012" 'nexus_provider_profile_c002_claude_authstability012' "$MAIN"
check_grep "unknown_nonterminal" '"UNKNOWN" -> {' "$MAIN"
check_grep "unauth_nonterminal" '"UNAUTHENTICATED" -> {' "$MAIN"
check_grep "stability_min_observations" 'CLAUDE_AUTH_STABLE_MIN_OBSERVATIONS = 2' "$MAIN"
check_grep "stability_min_ms" 'CLAUDE_AUTH_STABLE_MIN_MS = 1_500L' "$MAIN"
check_grep "stability_wait" 'AUTH_STABILITY_WAIT' "$MAIN"
check_grep "stability_pass" 'AUTH_STABILITY_PASS' "$MAIN"
check_grep "stable_describe" 'authenticated=true;stable=true' "$MAIN"
check_grep "execution_still_enabled" 'startExecutionProof(origin)' "$MAIN"
check_grep "preexecution_window_denied_nonterminal" 'onCreateWindowDeniedPreExecution' "$MAIN"
check_grep "execution_window_still_terminal" 'if (executionStarted && !terminalReceived)' "$MAIN"
check_grep "transport_preserved" 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' "$MAIN"
check_not_grep "diagnostic_noexec_guard_absent" 'CLAUDE_AUTH_DIAGNOSTIC_011_NO_EXECUTION' "$CLAUDE"

echo "CLAUDE_AUTH_STABILITY_012_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
