#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root}"; REF="${2:?reference020}"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"; CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"; MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"; BUILD="$ROOT/app/build.gradle.kts"
PASS=0; FAIL=0
check(){ local n="$1"; shift; if "$@"; then echo "PASS $n"; PASS=$((PASS+1)); else echo "FAIL $n"; FAIL=$((FAIL+1)); fi; }
contains(){ grep -Fq -- "$2" "$1"; }; absent(){ ! grep -Fq -- "$2" "$1"; }; same(){ cmp -s "$1" "$2"; }
check application_id_021 contains "$BUILD" 'applicationId = "nexus.android.c002.providerrunresume021"'
check version_021 contains "$BUILD" 'versionName = "0.0.22-c002-provider-run-resume021"'
check label_021 contains "$MANIFEST" 'android:label="NEXUS C002 PROVIDER RUN RESUME 021"'
check rotation_config_preserved contains "$MANIFEST" 'android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden"'
check stable_webview_profile contains "$MAIN" 'PROFILE_NAME = "nexus_provider_profile_c002_rotationrunstate019"'
check chatgpt_provider_byte_identical same "$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js" "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js"
check origin_policy_byte_identical same "$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt" "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
check web_bridge_byte_identical same "$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt" "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
check old_recreation_block_removed absent "$MAIN" 'ANDROID_INFLIGHT_RUN_RECREATION_DETECTED'
check resumable_inflight contains "$MAIN" 'priorState == RUN_STATE_IN_FLIGHT || priorState == RUN_STATE_RECOVERABLE'
check resume_metadata_mismatch_failclosed contains "$MAIN" 'ANDROID_RUN_RESUME_METADATA_MISMATCH'
check frozen_fingerprint_resume_check contains "$MAIN" 'ANDROID_RUN_RESUME_FROZEN_FINGERPRINT_MISMATCH'
check resume_attempt_bound contains "$MAIN" 'MAX_RESUME_ATTEMPTS = 2'
check resume_job_native contains "$MAIN" '.put("type", "RESUME_JOB")'
check resume_is_not_resubmit contains "$MAIN" 'resubmit=false'
check same_bridge_run_persisted contains "$MAIN" '.putString(RUN_LATCH_BRIDGE_RUN_ID_KEY, BRIDGE_RUN_ID)'
check same_job_persisted contains "$MAIN" '.putString(RUN_LATCH_JOB_ID_KEY, job.jobId)'
check provider_persisted contains "$MAIN" '.putString(RUN_LATCH_PROVIDER_KEY, "ANTHROPIC")'
check fingerprint_persisted contains "$MAIN" '.putString(RUN_LATCH_FINGERPRINT_KEY, job.frozenFingerprint)'
check phase_persisted contains "$MAIN" 'RUN_LATCH_PHASE_KEY'
check progress_refreshes_ownership contains "$MAIN" 'markRunProgress(jobStatus)'
check recoverable_state contains "$MAIN" 'RUN_STATE_RECOVERABLE = "RECOVERABLE"'
check no_question_persisted absent "$MAIN" '.putString("question"'
check no_handoff_persisted absent "$MAIN" '.putString("handoff"'
check no_cookie_persisted absent "$MAIN" '.putString("cookie"'
check no_secret_persisted absent "$MAIN" '.putString("secret"'
check resume_adapter_function contains "$CLAUDE" 'async function resumeJob(bridgeRunId,envelope)'
check resume_message_supported contains "$CLAUDE" "msg.type!=='EXECUTE_JOB' && msg.type!=='RESUME_JOB'"
check resume_observer_started contains "$CLAUDE" 'CLAUDE_RESUME_OBSERVER_STARTED'
check resume_response_capture contains "$CLAUDE" 'CLAUDE_RESUME_RESPONSE_CAPTURED'
check resume_result_tag contains "$CLAUDE" 'resumed:true'
check proof020_preserved contains "$CLAUDE" 'CLAUDE_UI_PROMPT_SENT_CONFIRMED__PROOF020__'
check stable_clear_preserved contains "$CLAUDE" 'Date.now()-clearedSince>=1500'
check rotation_handler_preserved contains "$MAIN" 'webview_preserved=true'
check resume_observer_no_mutation bash -c "python3 - '$CLAUDE' <<'PY'
from pathlib import Path
import re,sys
s=Path(sys.argv[1]).read_text(); m=re.search(r'async function resumeJob\(.*?\n  }\n\n  async function executeJob',s,re.S); assert m
b=m.group(0)
for x in ['setComposerText(', 'ensureComposerStateSynchronized(', '.click()', 'PROVIDER_UI_ACTUATE']: assert x not in b, x
PY"
check claude_provider_js_syntax node --check "$CLAUDE"
check main_changed bash -c "! cmp -s '$MAIN' '$REF/app/src/main/java/nexus/android/c002/MainActivity.kt'"
echo "PROVIDER_RUN_RESUME_SESSION_OWNERSHIP_021_STATIC_RESULT pass=$PASS fail=$FAIL"
test "$FAIL" -eq 0
