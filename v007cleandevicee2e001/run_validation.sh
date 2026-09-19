#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
PASS=0
FAIL=0
check(){ local name="$1"; shift; if "$@"; then echo "PASS $name"; PASS=$((PASS+1)); else echo "FAIL $name"; FAIL=$((FAIL+1)); fi; }
BG="$ROOT/app/build.gradle.kts"
MAN="$ROOT/app/src/main/AndroidManifest.xml"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
LAY="$ROOT/app/src/main/res/layout/activity_main.xml"
CHAT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
ORIGIN="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
check app_id grep -Fq 'applicationId = "nexus.android.v007.cleandevicee2e001"' "$BG"
check version grep -Fq 'versionName = "0.0.30-v007-clean-device-e2e001"' "$BG"
check label grep -Fq 'android:label="NEXUS V007 CLEAN DEVICE E2E 001"' "$MAN"
check unique_profile grep -Fq 'nexus_provider_profile_v007_clean_device_e2e_001' "$MAIN"
check old_profile_absent bash -c "! grep -Fq 'nexus_provider_profile_c002_executionproof006_uiretry1' '$MAIN'"
check v007_job grep -Fq 'V007-CLEAN-DEVICE-E2E-001-JOB-001' "$MAIN"
check v007_pack grep -Fq 'V007_ANDROID_CLEAN_DEVICE_E2E_001_V1' "$MAIN"
check v007_token grep -Fq 'NEXUS_V007_CLEAN_DEVICE_E2E_001_OK' "$MAIN"
check chatgpt_selected grep -Fq 'provider = SelectedProvider.CHATGPT' "$MAIN"
check external_research_false grep -Fq '.put("external_research", false)' "$MAIN"
check canonical_write_false grep -Fq '.put("canonical_write", false)' "$MAIN"
check state_mutation_none grep -Fq '.put("state_mutation_mode", "NONE")' "$MAIN"
check truth_winner_none grep -Fq '.put("truth_winner", "NONE")' "$MAIN"
check terminal_receipt grep -Fq 'TERMINAL_RECEIPT_PASS' "$MAIN"
check pass_headline grep -Fq 'EXECUTION PROOF PASS — STOP GATE' "$MAIN"
check compact_layout grep -Fq 'android:maxLines="2"' "$LAY"
check auth_google_exact grep -Fq 'host == "accounts.google.com"' "$ORIGIN"
# Security invariants are already exercised by the inherited UIRETRY1 validator;
# keep V007-specific validation focused on the new sandbox/profile/contract identity.
check chat_js_syntax node --check "$CHAT"
check bridge_exists test -s "$BRIDGE"
echo "V007_CLEAN_DEVICE_E2E001_STATIC_RESULT pass=$PASS fail=$FAIL"
test "$FAIL" -eq 0
