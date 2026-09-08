#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"
REF="${2:?reference016}"
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
check web_bridge_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
grep_ok identity_017 'nexus_provider_profile_c002_claude_turngeneration017' "$MAIN"
grep_ok application_id_017 'applicationId = "nexus.android.c002.claudeturngeneration017"' "$GRADLE"
grep_ok version_017 'versionName = "0.0.18-c002-claude-turngeneration017"' "$GRADLE"
grep_ok label_017 'android:label="NEXUS C002 CLAUDE TURN GENERATION DIAG 017"' "$MANIFEST"
grep_ok proof_token_017 'NEXUS_CLAUDE_TURN_GENERATION_DIAGNOSTIC_017_OK' "$MAIN"
grep_ok fingerprint_contract_preserved '.put("analysis_fingerprint", job.frozenFingerprint)' "$MAIN"
grep_ok turn_snapshot 'function turnGenerationSnapshot(envelope)' "$PROV"
grep_ok turn_compact 'function compactTurnDiag(d)' "$PROV"
grep_ok turn_wait 'function waitForTurnAndGeneration(bridgeRunId,envelope,baseline,timeout=30000)' "$PROV"
grep_ok baseline_progress "CLAUDE_TURN_BASELINE__'+compactTurnDiag(turnBaseline)" "$PROV"
grep_ok generation_progress "CLAUDE_GENERATION_OBSERVED__'+text" "$PROV"
grep_ok user_turn_terminal 'CLAUDE_USER_TURN_NOT_MATERIALIZED_AFTER_SUBMISSION__' "$PROV"
grep_ok generation_terminal 'CLAUDE_GENERATION_NOT_OBSERVED_AFTER_SUBMISSION__' "$PROV"
grep_ok wait_inserted 'await waitForTurnAndGeneration(bridgeRunId,envelope,turnBaseline);' "$PROV"
grep_ok prompt_confirmation_preserved 'CLAUDE_UI_PROMPT_SENT_CONFIRMED__' "$PROV"
grep_ok prompt_retry_preserved 'CLAUDE_UI_PROMPT_RETRY_1' "$PROV"
grep_ok result_diag_preserved 'function diagnoseResultDom(envelope)' "$PROV"
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

echo "CLAUDE_TURN_GENERATION_DIAGNOSTIC_017_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
