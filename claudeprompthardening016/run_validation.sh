#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"
REF="${2:?reference015}"
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
grep_ok identity_016 'nexus_provider_profile_c002_claude_promptsubmission016' "$MAIN"
grep_ok application_id_016 'applicationId = "nexus.android.c002.claudeprompthardening016"' "$GRADLE"
grep_ok version_016 'versionName = "0.0.17-c002-claude-prompthardening016"' "$GRADLE"
grep_ok label_016 'android:label="NEXUS C002 CLAUDE PROMPT HARDENING 016"' "$MANIFEST"
grep_ok proof_token_016 'NEXUS_CLAUDE_PROMPT_SUBMISSION_HARDENING_016_OK' "$MAIN"
grep_ok contract_fingerprint_added '.put("analysis_fingerprint", job.frozenFingerprint)' "$MAIN"
grep_ok parser_fingerprint_gate_preserved 'if(parsed.audit?.analysis_fingerprint!==envelope.frozen_fingerprint) continue;' "$PROV"
grep_ok result_prefilter_preserved 'if(!text.includes(envelope.frozen_fingerprint)) continue;' "$PROV"
grep_ok prompt_signal_helper 'function promptSubmissionSignal(envelope)' "$PROV"
grep_ok prompt_wait_helper 'async function waitForPromptSubmission(envelope,timeout)' "$PROV"
grep_ok prompt_first_click_status 'CLAUDE_UI_PROMPT_CLICK_1' "$PROV"
grep_ok prompt_retry_status 'CLAUDE_UI_PROMPT_RETRY_1' "$PROV"
grep_ok prompt_confirmed_status 'CLAUDE_UI_PROMPT_SENT_CONFIRMED__' "$PROV"
grep_ok prompt_fail_closed 'CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED' "$PROV"
grep_ok retry_requeries_button 'send=findSendButton();' "$PROV"
grep_ok primary_wait_bounded 'waitForPromptSubmission(envelope,4000)' "$PROV"
grep_ok retry_wait_bounded 'waitForPromptSubmission(envelope,6000)' "$PROV"
grep_absent optimistic_prompt_sent "await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT');" "$PROV"
grep_absent global_submit_selector "'button[type=\"submit\"]'" "$PROV"
grep_ok oauth_passive_wait_preserved 'OAUTH_HANDOFF_PASSIVE_WAIT_MS = 6_000L' "$MAIN"
grep_ok oauth_fallback_wait_preserved 'OAUTH_HANDOFF_FALLBACK_WAIT_MS = 8_000L' "$MAIN"
grep_ok popup_grace_preserved 'AUTH_POPUP_DESTROY_GRACE_MS = 750L' "$MAIN"
grep_ok transport_preserved 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' "$MAIN"
grep_ok diagnostic_015_preserved 'function diagnoseResultDom(envelope)' "$PROV"

if python3 - "$REF/app/src/main/assets/nexus/claude_provider_c002.js" "$PROV" <<'PY'
import re,sys
ref=open(sys.argv[1]).read(); cur=open(sys.argv[2]).read()
def result_selectors(src):
    a=src.index('function findResultCandidates(envelope)')
    b=src.index('async function progress',a)
    block=src[a:b]
    return set(re.findall(r"['\"]([^'\"]*(?:message|assistant|streaming|\\.prose|article|main div)[^'\"]*)['\"]", block))
assert result_selectors(ref)==result_selectors(cur), (result_selectors(ref),result_selectors(cur))
PY
then ok result_selector_set_unchanged; else bad result_selector_set_unchanged; fi

if python3 - "$PROV" <<'PY'
import sys
s=open(sys.argv[1]).read()
a=s.index("CLAUDE_UI_PROMPT_SENT_CONFIRMED__")
b=s.index('const result=await waitForStableJson',a)
assert a < b
PY
then ok response_polling_after_submission_confirmation; else bad response_polling_after_submission_confirmation; fi

if node --check "$PROV" >/dev/null; then ok claude_provider_js_syntax; else bad claude_provider_js_syntax; fi

echo "CLAUDE_PROMPT_SUBMISSION_HARDENING_016_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
