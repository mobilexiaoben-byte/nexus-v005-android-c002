#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
PASS=0
FAIL=0
check(){ local name="$1"; shift; if "$@"; then echo "PASS $name"; PASS=$((PASS+1)); else echo "FAIL $name"; FAIL=$((FAIL+1)); fi; }
BG="$ROOT/app/build.gradle.kts"
MAN="$ROOT/app/src/main/AndroidManifest.xml"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
CHAT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
ORIGIN="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
check app_id grep -Fq 'applicationId = "nexus.android.v007.cleandevicee2e001.failclosed1"' "$BG"
check version grep -Fq 'versionName = "0.0.33-v007-clean-device-e2e001-failclosed1"' "$BG"
check label grep -Fq 'android:label="NEXUS V007 FAIL-CLOSED 1"' "$MAN"
check unique_profile grep -Fq 'nexus_provider_profile_v007_clean_device_e2e_001_failclosed1' "$MAIN"
check failclosed_job grep -Fq 'V007-CLEAN-DEVICE-E2E-001-FAILCLOSED1-JOB-001' "$MAIN"
check failclosed_pack grep -Fq 'V007_ANDROID_CLEAN_DEVICE_E2E_001_FAILCLOSED1_V1' "$MAIN"
check expected_token grep -Fq 'NEXUS_V007_CLEAN_DEVICE_E2E_001_FAILCLOSED1_EXPECTED_OK' "$MAIN"
check injected_wrong_token grep -Fq 'NEXUS_V007_FAILCLOSED_INJECTED_WRONG_ANSWER' "$MAIN"
check injection_event grep -Fq 'FAILCLOSED_FAULT_INJECTED' "$MAIN"
check injection_statement grep -Fq 'resultPack.put("answer", FAILCLOSED_INJECTED_ANSWER)' "$MAIN"
check answer_mismatch_gate grep -Fq 'if (resultPack.optString("answer") != PROOF_TOKEN) return "ANDROID_RESULT_ANSWER_MISMATCH"' "$MAIN"
check injection_before_validation python3 - "$MAIN" <<'PY'
import sys
s=open(sys.argv[1], encoding='utf-8').read()
a=s.index('resultPack.put("answer", FAILCLOSED_INJECTED_ANSWER)')
b=s.index('val packValidation = validateResultPack(job, resultPack)')
raise SystemExit(0 if a < b else 1)
PY
check chatgpt_selected grep -Fq 'provider = SelectedProvider.CHATGPT' "$MAIN"
check external_research_false grep -Fq '.put("external_research", false)' "$MAIN"
check canonical_write_false grep -Fq '.put("canonical_write", false)' "$MAIN"
check state_mutation_none grep -Fq '.put("state_mutation_mode", "NONE")' "$MAIN"
check truth_winner_none grep -Fq '.put("truth_winner", "NONE")' "$MAIN"
check block_headline grep -Fq 'currentHeadline = "BLOCKED — $code"' "$MAIN"
check terminal_pass_path_unchanged grep -Fq 'TERMINAL_RECEIPT_PASS' "$MAIN"
check authoritative_profile_marker grep -Fq 'data-testid="accounts-profile-button"' "$CHAT"
check auto_probe_mode grep -Fq "mode:'AUTO_AUTH_MENU_PROBE'" "$CHAT"
check menu_not_auth_proof grep -Fq 'MENU_CLICK_IS_NOT_AUTH_PROOF' "$CHAT"
check menu_click_false_meta grep -Fq 'menu_click_is_auth_proof:false' "$CHAT"
check unique_menu_gate grep -Fq 'matches.length===1?matches[0]:null' "$CHAT"
check unknown_stability grep -Fq 'Date.now()-authProbeUnknownSince<2500' "$CHAT"
check one_probe_gate grep -Fq 'if(authProbeAttempted) return;' "$CHAT"
check no_execution_from_probe bash -c "! sed -n '/function maybeAutoOpenAuthMenu/,/^  }/p' '$CHAT' | grep -Fq 'executeJob'"
check exact_chatgpt_origin grep -Fq 'const val CHATGPT_ORIGIN = "https://chatgpt.com"' "$MAIN"
check auth_google_exact grep -Fq 'host == "accounts.google.com"' "$ORIGIN"
check no_webview_debug bash -c "! grep -Fq 'setWebContentsDebuggingEnabled(true)' '$MAIN'"
check node_syntax node --check "$CHAT"
check bridge_exists test -s "$BRIDGE"
echo "V007_FAILCLOSED1_STATIC_RESULT pass=$PASS fail=$FAIL"
test "$FAIL" -eq 0
