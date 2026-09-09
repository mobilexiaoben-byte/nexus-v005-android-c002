#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root020}"
REF="${2:?reference019}"
PROV="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
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

check mainactivity_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/MainActivity.kt" "$MAIN"
check chatgpt_provider_byte_identical cmp -s "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$CHATGPT"
check origin_policy_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$ORIGIN"
check web_bridge_byte_identical cmp -s "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$BRIDGE"
grep_ok application_id_020 'applicationId = "nexus.android.c002.claudesubmissionproof020"' "$GRADLE"
grep_ok version_020 'versionName = "0.0.21-c002-claude-submission-proof020"' "$GRADLE"
grep_ok label_020 'android:label="NEXUS C002 CLAUDE SUBMISSION PROOF 020"' "$MANIFEST"
grep_ok rotation_config_preserved 'android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden"' "$MANIFEST"

grep_absent old_prompt_submission_signal 'function promptSubmissionSignal(envelope)' "$PROV"
grep_absent old_wait_prompt_submission 'function waitForPromptSubmission(envelope,timeout)' "$PROV"
grep_absent bare_composer_cleared_return "return 'COMPOSER_CLEARED'" "$PROV"
grep_absent old_not_confirmed_error 'CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED' "$PROV"

grep_ok submission_snapshot 'function composerSubmissionSnapshot(envelope,baseline)' "$PROV"
grep_ok compact_proof "'S020'" "$PROV"
grep_ok stable_clear_1500 'Date.now()-clearedSince>=1500' "$PROV"
grep_ok cleared_requires_pack_absent 'const composerCleared=!!composer && !hasPack && !hasTail && text.length<80' "$PROV"
grep_ok user_turn_delta 'const userTurn=(turn.po>baseline.po || turn.u>baseline.u)' "$PROV"
grep_ok generation_delta 'const generation=(turn.g===1 || turn.s>baseline.s || turn.st>baseline.st || turn.a>baseline.a)' "$PROV"
grep_ok establish_requires_two_axes 'if(stableCleared && (latest.user_turn || latest.generation))' "$PROV"
grep_ok established_event 'CLAUDE_SUBMISSION_ESTABLISHED__' "$PROV"
grep_ok proof_telemetry 'CLAUDE_SUBMISSION_PROOF__' "$PROV"

grep_ok retry_guard 'const retryAllowed=!!snap && snap.has_pack && !snap.user_turn && !snap.generation' "$PROV"
grep_ok unsafe_retry_block 'CLAUDE_PROMPT_SUBMISSION_NOT_ESTABLISHED_NO_SAFE_RETRY__' "$PROV"
grep_ok terminal_not_established 'CLAUDE_PROMPT_SUBMISSION_NOT_ESTABLISHED__' "$PROV"
grep_ok confirmed_proof020 'CLAUDE_UI_PROMPT_SENT_CONFIRMED__PROOF020__' "$PROV"

grep_ok provider_ui_actuation_preserved 'PROVIDER_UI_ACTUATE' "$PROV"
grep_ok page_world_sync_preserved 'PROVIDER_COMPOSER_SYNC_PASS__PAGE_WORLD_' "$PROV"
grep_ok turn_generation_gate_preserved 'waitForTurnAndGeneration(bridgeRunId,envelope,turnBaseline)' "$PROV"
grep_ok stable_json_gate_preserved 'waitForStableJson(bridgeRunId,envelope)' "$PROV"
grep_ok expected_proof_token_preserved 'NEXUS_PROVIDER_COMPOSER_STATE_SYNC_018_OK' "$MAIN"

if node --check "$PROV" >/dev/null; then ok claude_provider_js_syntax; else bad claude_provider_js_syntax; fi
if python3 - "$PROV" <<'PY'
import sys
s=open(sys.argv[1]).read()
a=s.index("let submission=await waitForSubmissionEstablished")
b=s.index("await waitForTurnAndGeneration",a)
block=s[a:b]
assert "if(!submission.mode)" in block
assert "CLAUDE_UI_PROMPT_SENT_CONFIRMED__PROOF020__" in block
assert block.index("if(!submission.mode)") < block.rindex("CLAUDE_UI_PROMPT_SENT_CONFIRMED__PROOF020__")
assert "waitForPromptSubmission" not in s
assert "return 'COMPOSER_CLEARED'" not in s
PY
then ok confirmed_only_after_proof_mode; else bad confirmed_only_after_proof_mode; fi

echo "CLAUDE_SUBMISSION_STATE_PROOF_HARDENING_020_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
