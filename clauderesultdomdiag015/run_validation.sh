#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"
REF="${2:?reference014}"
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
grep_absent(){ local n="$1" p="$2" f="$3"; if grep -Fq "$p" "$f"; then bad "$n"; else ok "$n"; fi; }

check chatgpt_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check origin_policy_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
check web_bridge_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
grep_ok identity_015 'nexus_provider_profile_c002_claude_resultdomdiag015' "$MAIN"
grep_ok application_id_015 'applicationId = "nexus.android.c002.clauderesultdomdiag015"' "$GRADLE"
grep_ok version_015 'versionName = "0.0.16-c002-claude-resultdomdiag015"' "$GRADLE"
grep_ok label_015 'android:label="NEXUS C002 CLAUDE RESULT DOM DIAG 015"' "$MANIFEST"
grep_ok proof_token_015 'NEXUS_CLAUDE_RESULT_DOM_DIAGNOSTIC_015_OK' "$MAIN"
grep_ok diagnostic_scanner 'function diagnoseResultDom(envelope)' "$PROV"
grep_ok compact_diag 'function compactDomDiag(d)' "$PROV"
grep_ok diagnostic_correlated_progress 'await progress(bridgeRunId,diagText)' "$PROV"
grep_ok diagnostic_rate_bound 'Date.now()-lastDiagAt>=5000' "$PROV"
grep_ok wait_bridge_run_id 'waitForStableJson(bridgeRunId,envelope' "$PROV"
grep_ok timeout_contains_diag "CLAUDE_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__'+compactDomDiag" "$PROV"
grep_ok diag_contract_fingerprint_flag 'expected?.audit?.analysis_fingerprint===envelope.frozen_fingerprint' "$PROV"
grep_ok original_fingerprint_prefilter 'if(!text.includes(envelope.frozen_fingerprint)) continue;' "$PROV"
grep_ok original_parse_fingerprint_gate 'if(parsed.audit?.analysis_fingerprint!==envelope.frozen_fingerprint) continue;' "$PROV"
grep_ok original_parse_pack_gate 'if(parsed.pack_id!==envelope.context_pack_id) continue;' "$PROV"
grep_ok original_parse_comparison_gate 'if(parsed.comparison_id!==envelope.frozen_package?.comparison_id) continue;' "$PROV"
grep_ok original_provider_gate "toUpperCase()!=='ANTHROPIC'" "$PROV"
grep_absent contract_still_omits_audit_fingerprint '.put("analysis_fingerprint"' "$MAIN"
grep_ok oauth_passive_wait_preserved 'OAUTH_HANDOFF_PASSIVE_WAIT_MS = 6_000L' "$MAIN"
grep_ok oauth_fallback_wait_preserved 'OAUTH_HANDOFF_FALLBACK_WAIT_MS = 8_000L' "$MAIN"
grep_ok popup_grace_preserved 'AUTH_POPUP_DESTROY_GRACE_MS = 750L' "$MAIN"
grep_ok transport_preserved 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' "$MAIN"
grep_ok execution_still_enabled 'type == "PROVIDER_PROGRESS" -> handleProviderProgress(message)' "$MAIN"

if python3 - "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$PROV" <<'PY'
import re,sys
ref=open(sys.argv[1]).read(); cur=open(sys.argv[2]).read()
def set_for_find(src):
    a=src.index('function findResultCandidates(envelope)')
    b=src.index('async function progress',a)
    block=src[a:b]
    return set(re.findall(r"['\"]([^'\"]*(?:message|assistant|streaming|\\.prose|article|main div)[^'\"]*)['\"]", block))
assert set_for_find(ref)==set_for_find(cur), (set_for_find(ref),set_for_find(cur))
PY
then ok result_selector_set_unchanged; else bad result_selector_set_unchanged; fi

echo "CLAUDE_RESULT_DOM_DIAGNOSTIC_015_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
