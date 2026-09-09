#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root required}"
REF="${2:?022 reference required}"
pass=0; fail=0
check(){ local n="$1"; shift; if "$@"; then echo "PASS $n"; pass=$((pass+1)); else echo "FAIL $n"; fail=$((fail+1)); fi; }
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
GRADLE="$ROOT/app/build.gradle.kts"
MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"
LAYOUT="$ROOT/app/src/main/res/layout/activity_main.xml"
CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
CHATGPT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
ORIGIN="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
check application_id_023 grep -Fq 'applicationId = "nexus.android.c002.runresumeevidence023"' "$GRADLE"
check version_023 grep -Fq 'versionCode = 24' "$GRADLE"
check version_name_023 grep -Fq '0.0.24-c002-run-resume-evidence023' "$GRADLE"
check label_023 grep -Fq 'NEXUS C002 RUN RESUME EVIDENCE 023' "$MANIFEST"
check evidence_panel_layout grep -Fq 'android:id="@+id/runEvidence"' "$LAYOUT"
check evidence_panel_non_scrolling grep -Fq 'android:maxLines="5"' "$LAYOUT"
check evidence_binding grep -Fq 'runEvidence = findViewById(R.id.runEvidence)' "$MAIN"
check evidence_renderer grep -Fq 'private fun renderRunEvidence()' "$MAIN"
check evidence_mode_line grep -Fq 'EVIDENCE 023 | MODE=' "$MAIN"
check same_run_visible grep -Fq 'SAME_RUN=' "$MAIN"
check resubmit_visible grep -Fq 'RESUBMIT=' "$MAIN"
check execute_count_visible grep -Fq 'EXECUTE_JOB=' "$MAIN"
check resume_count_visible grep -Fq 'RESUME_JOB=' "$MAIN"
check injection_count_visible grep -Fq 'PROMPT_INJECTION=' "$MAIN"
check send_count_visible grep -Fq 'SEND_CLICK=' "$MAIN"
check fresh_execute_one grep -Fq 'putInt(RUN_EVIDENCE_EXECUTE_COUNT_KEY, 1)' "$MAIN"
check resume_counter_increment grep -Fq 'resumeDispatchCount = runLatch.getInt(RUN_EVIDENCE_RESUME_COUNT_KEY, 0) + 1' "$MAIN"
check resume_same_run_yes grep -Fq 'putString(RUN_EVIDENCE_SAME_RUN_KEY, "YES")' "$MAIN"
check resume_resubmit_false grep -Fq 'putString(RUN_EVIDENCE_RESUBMIT_KEY, "FALSE")' "$MAIN"
check resume_job_023 grep -Fq 'recordDiagnostic("RESUME_JOB_023"' "$MAIN"
check resume_observer_only grep -Fq 'RUN RESUME 023 — OBSERVER ONLY / SAME CLAUDE CONVERSATION' "$MAIN"
check prompt_ready_maps_injection grep -Fq 'jobStatus == "CLAUDE_UI_PROMPT_READY"' "$MAIN"
check click1_maps_send grep -Fq 'jobStatus == "CLAUDE_UI_PROMPT_CLICK_1"' "$MAIN"
check click2_maps_send grep -Fq 'jobStatus == "CLAUDE_UI_PROMPT_CLICK_2"' "$MAIN"
check retry_click2_emitted grep -Fq "progress(bridgeRunId,'CLAUDE_UI_PROMPT_CLICK_2')" "$CLAUDE"
check resume_adapter_preserved grep -Fq 'CLAUDE_RESUME_OBSERVER_STARTED' "$CLAUDE"
check recoverable_preserved grep -Fq 'RECOVERABLE — CLOSE AND REOPEN NEXUS NOW' "$MAIN"
check stable_webview_profile grep -Fq 'nexus_provider_profile_c002_rotationrunstate019' "$MAIN"
check chatgpt_identical cmp -s "$CHATGPT" "$REF/app/src/main/assets/nexus/chatgpt_provider_c002.js"
check origin_identical cmp -s "$ORIGIN" "$REF/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
check bridge_identical cmp -s "$BRIDGE" "$REF/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
check claude_only_click2_added python3 - "$CLAUDE" "$REF/app/src/main/assets/nexus/claude_provider_c002.js" <<'PY'
import sys
cur=open(sys.argv[1]).read(); ref=open(sys.argv[2]).read()
line="        await progress(bridgeRunId,'CLAUDE_UI_PROMPT_CLICK_2');\n"
assert cur.count(line)==1
assert cur.replace(line,'')==ref
PY
check no_prompt_persisted bash -c "! grep -q 'RUN_LATCH_QUESTION\|PROOF_QUESTION.*putString\|PROOF_HANDOFF.*putString' '$MAIN'"
check no_cookie_persisted bash -c "! grep -qi 'putString.*cookie' '$MAIN'"
check claude_js_syntax node --check "$CLAUDE"
echo "RUN_RESUME_EVIDENCE_023_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
