#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
MON="$ROOT/app/src/main/java/nexus/android/c002/core/U002Monitor.kt"
GRADLE="$ROOT/app/build.gradle.kts"
MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"
pass=0; fail=0
check(){ if eval "$2"; then echo "PASS $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); fi; }
check isolated_app_id "grep -Fq 'applicationId = \"nexus.android.c002.u002monitor001\"' \"$GRADLE\""
check isolated_version "grep -Fq 'versionName = \"0.0.29-u002-android-monitor001\"' \"$GRADLE\""
check isolated_label "grep -Fq 'NEXUS U002 ANDROID MONITOR TEST' \"$MANIFEST\""
check monitor_contract "grep -Fq 'U002_ANDROID_MONITOR_V1' \"$MON\""
check monitor_jsonl "grep -Fq 'u002_monitor_events.jsonl' \"$MON\""
check terminal_event "grep -Fq 'TERMINAL_RECEIPT_PASS' \"$MAIN\""
check job_corr "grep -Fq '\"job_id\" to job.jobId' \"$MAIN\""
check bridge_corr "grep -Fq '\"bridge_run_id\" to BRIDGE_RUN_ID' \"$MAIN\""
check pack_corr "grep -Fq '\"context_pack_id\" to job.contextPackId' \"$MAIN\""
check fingerprint_corr "grep -Fq '\"frozen_fingerprint\" to job.frozenFingerprint' \"$MAIN\""
check no_canonical_write "grep -Fq '\"canonical_write\" to false' \"$MAIN\""
check no_state_mutation "grep -Fq '\"state_mutation_mode\" to \"NONE\"' \"$MAIN\""
check fail_closed "grep -Fq 'u002Monitor.record(\"FAIL_CLOSED\"' \"$MAIN\""
check transport_preserved "grep -Fq 'ANDROID_WEBVIEW_CHROMIUM_BRIDGE' \"$MAIN\""
check zai_transport_preserved "grep -Fq 'SelectedProvider.ZAI' \"$MAIN\""
echo "U002_ANDROID_MONITOR_STATIC_RESULT pass=$pass fail=$fail"
test "$fail" -eq 0
