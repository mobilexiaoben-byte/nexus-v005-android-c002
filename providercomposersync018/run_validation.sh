#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root018}"
REF="${2:?reference017}"
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

check chatgpt_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check origin_policy_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
grep_ok identity_018 'nexus_provider_profile_c002_provider_composersync018' "$MAIN"
grep_ok application_id_018 'applicationId = "nexus.android.c002.providercomposersync018"' "$GRADLE"
grep_ok version_018 'versionName = "0.0.19-c002-provider-composersync018"' "$GRADLE"
grep_ok label_018 'android:label="NEXUS C002 PROVIDER COMPOSER SYNC 018"' "$MANIFEST"
grep_ok proof_token_018 'NEXUS_PROVIDER_COMPOSER_STATE_SYNC_018_OK' "$MAIN"
grep_ok generic_ui_actuate_type 'type == "PROVIDER_UI_ACTUATE" -> handleProviderUiActuate' "$MAIN"
grep_ok generic_ui_action_gate 'message.optString("action") != "SET_COMPOSER_TEXT"' "$MAIN"
grep_ok ui_actuate_correlation 'ANDROID_UI_ACTUATE_CORRELATION_MISMATCH' "$MAIN"
grep_ok ui_actuate_payload_binding '!text.contains(job.contextPackId) || !text.contains(job.frozenFingerprint)' "$MAIN"
grep_ok ui_actuate_selector_bounds 'arr.length() !in 1..12' "$MAIN"
grep_ok page_world_executor 'fun executePageWorld(origin: String, script: String, onResult: (String) -> Unit): Boolean' "$BRIDGE"
grep_ok page_world_origin_gate 'if (!OriginPolicy.isBridgeOriginAllowed(origin)) return false' "$BRIDGE"
grep_ok page_world_current_url_gate 'if (currentUrl != origin && !currentUrl.startsWith("$origin/")) return false' "$BRIDGE"
if grep -Fq 'addJavascriptInterface' "$BRIDGE"; then bad no_addJavascriptInterface_absent; else ok no_addJavascriptInterface_absent; fi
grep_ok adapter_composer_contract 'const COMPOSER_SELECTORS=[' "$PROV"
grep_ok adapter_send_contract 'const SEND_SELECTORS=[' "$PROV"
grep_ok desktop_send_selector_priority 'button[data-testid="chat-input-send"]' "$PROV"
grep_ok semantic_send_state 'function buttonSemanticState(el)' "$PROV"
grep_ok semantic_aria_disabled "getAttribute('aria-disabled')" "$PROV"
grep_ok semantic_data_disabled "getAttribute('data-disabled')" "$PROV"
grep_ok page_world_request 'function requestPageWorldComposerActuation(bridgeRunId,prompt,timeout=8000)' "$PROV"
grep_ok isolated_first 'waitForSendReady(composer,1500)' "$PROV"
grep_ok page_world_fallback 'PROVIDER_COMPOSER_SYNC_FALLBACK__PAGE_WORLD' "$PROV"
grep_ok composer_sync_fail_closed 'CLAUDE_COMPOSER_STATE_NOT_SYNCHRONIZED__' "$PROV"
grep_ok ui_actuate_result_handler "msg.type==='PROVIDER_UI_ACTUATE_RESULT'" "$PROV"
grep_ok retry_semantic_gate '!buttonSemanticState(send).ready' "$PROV"
grep_ok turn_generation_preserved 'await waitForTurnAndGeneration(bridgeRunId,envelope,turnBaseline);' "$PROV"
grep_ok prompt_confirmation_preserved 'CLAUDE_UI_PROMPT_SENT_CONFIRMED__' "$PROV"
grep_ok result_diag_preserved 'function diagnoseResultDom(envelope)' "$PROV"
grep_ok oauth_passive_wait_preserved 'OAUTH_HANDOFF_PASSIVE_WAIT_MS' "$MAIN"
grep_ok transport_preserved 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' "$MAIN"

if python3 - "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$PROV" <<'PY'
import sys
ref=open(sys.argv[1]).read(); cur=open(sys.argv[2]).read()
def block(src):
    a=src.index('function findResultCandidates(envelope)')
    b=src.index('async function progress',a)
    return src[a:b]
assert block(ref)==block(cur)
PY
then ok result_extractor_block_unchanged; else bad result_extractor_block_unchanged; fi

if python3 - "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE" <<'PY'
import sys,re
ref=open(sys.argv[1]).read(); cur=open(sys.argv[2]).read()
cur=re.sub(r'\n    fun executePageWorld\(origin: String, script: String, onResult: \(String\) -> Unit\): Boolean \{.*?\n    \}\n','',cur,flags=re.S)
assert ref==cur
PY
then ok web_bridge_only_bounded_page_world_method_added; else bad web_bridge_only_bounded_page_world_method_added; fi

if node --check "$PROV" >/dev/null 2>&1; then ok claude_provider_js_syntax; else bad claude_provider_js_syntax; fi

echo "PROVIDER_COMPOSER_STATE_SYNC_018_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
