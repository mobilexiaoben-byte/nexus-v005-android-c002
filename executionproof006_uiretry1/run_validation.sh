#!/usr/bin/env bash
set -euo pipefail
ROOT="$1"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
POLICY="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
CHAT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
PASS=0; FAIL=0
check(){ local id="$1"; shift; if "$@"; then echo "PASS $id"; PASS=$((PASS+1)); else echo "FAIL $id"; FAIL=$((FAIL+1)); fi; }
contains(){ grep -Fq "$2" "$1"; }
count_is(){ local f="$1" needle="$2" expected="$3"; test "$(grep -Foc "$needle" "$f" || true)" -eq "$expected"; }

check U01_package contains "$ROOT/app/build.gradle.kts" 'applicationId = "nexus.android.c002.executionproof006.uiretry1"'
check U02_version contains "$ROOT/app/build.gradle.kts" 'versionCode = 10'
check U03_label contains "$ROOT/app/src/main/AndroidManifest.xml" 'NEXUS C002 EXECUTION PROOF 006 UIRETRY1'
check U04_profile contains "$MAIN" 'nexus_provider_profile_c002_executionproof006_uiretry1'
check U05_google_com_exact contains "$POLICY" 'host == "accounts.google.com"'
check U06_youtube_exact contains "$POLICY" 'host == "accounts.youtube.com"'
check U07_google_fr_exact contains "$POLICY" 'host == "accounts.google.fr"'
check U08_no_google_com_wildcard bash -c "! grep -Fq 'endsWith(\".google.com\")' '$POLICY'"
check U09_no_youtube_wildcard bash -c "! grep -Fq 'endsWith(\".youtube.com\")' '$POLICY'"
check U10_no_google_fr_wildcard bash -c "! grep -Fq 'endsWith(\".google.fr\")' '$POLICY'"
check U11_no_plain_google_fr bash -c "! grep -Fq 'host == \"google.fr\"' '$POLICY'"
check U12_https_only contains "$POLICY" 'if (!uri.scheme.equals("https", ignoreCase = true)) return false'
check U13_bridge_origins_clean python3 -c "s=open('$POLICY').read(); bridge=s.split('fun isBridgeOriginAllowed',1)[0]; assert 'google' not in bridge and 'youtube' not in bridge"
check U14_bridge_unchanged bash -c "cd '$ROOT' && echo 'a842eb5d15d23b0ace09674585cefbfba2a753c155eeb5b0c0df6aaf9324275a  app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt' | sha256sum -c - >/dev/null"
check U15_claude_unchanged bash -c "cd '$ROOT' && echo 'f1dc78cdbadcc252a529c2db86b15ac42a92f0f2c132181cd1072bc24b131366  app/src/main/assets/nexus/claude_provider_c002.js' | sha256sum -c - >/dev/null"
check U16_core_contract_unchanged bash -c "cd '$ROOT' && echo '408487cffd660e5446c6362e272dd04395c70a575048fa1320c02819845b2a85  app/src/main/java/nexus/android/c002/core/TransportContract.kt' | sha256sum -c - >/dev/null"
check U17_ui_error_detector contains "$CHAT" 'function detectUiResponseError()'
check U18_retry_button_detector contains "$CHAT" 'function findRetryButton()'
check U19_retry_fr contains "$CHAT" "'réessayer'"
check U20_retry_en contains "$CHAT" "'retry'"
check U21_ui_error_code contains "$CHAT" 'CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE'
check U22_no_retry_error_code contains "$CHAT" 'CHATGPT_UI_RESPONSE_ERROR_NO_RETRY_CONTROL'
check U23_retry_control_lost contains "$CHAT" 'CHATGPT_UI_RESPONSE_ERROR_RETRY_CONTROL_LOST'
check U24_retry_after_error contains "$CHAT" "if(firstCode!=='CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE') throw firstErr"
check U25_retry_click_once count_is "$CHAT" 'retry.click();' 1
check U26_retry_counter_once count_is "$CHAT" 'retryCount=1;' 1
check U27_retry_progress_detected contains "$CHAT" "CHATGPT_UI_RESPONSE_ERROR_DETECTED"
check U28_retry_progress_triggered contains "$CHAT" "CHATGPT_UI_RETRY_1_TRIGGERED"
check U29_first_wait_bounded contains "$CHAT" 'waitForAssistantResult(beforeCount,80000)'
check U30_retry_wait_bounded contains "$CHAT" 'waitForAssistantResult(beforeCount,80000,graceUntil)'
check U31_retry_grace contains "$CHAT" 'const graceUntil=Date.now()+5000'
check U32_retry_terminal_error contains "$CHAT" 'CHATGPT_UI_RESPONSE_ERROR_AFTER_RETRY'
check U33_retry_meta contains "$CHAT" 'retry_count:retryCount'
check U34_retry_policy_meta contains "$CHAT" "retry_policy:'EXPLICIT_UI_ERROR_ONLY__MAX_1'"
check U35_describe_before_execute python3 -c "s=open('$MAIN').read(); assert s.index('describePassed = true') < s.index('startExecutionProof(origin)') < s.index('.put(\"type\", \"EXECUTE_JOB\")')"
check U36_ack_gate contains "$MAIN" 'RuntimeGate.validateAck'
check U37_terminal_receipt contains "$MAIN" 'TERMINAL_RECEIPT_PASS'
check U38_single_job_guard contains "$MAIN" 'if (!describePassed || executionStarted || proofStopped) return'
check U39_external_false contains "$MAIN" '.put("external_research", false)'
check U40_canonical_false contains "$MAIN" '.put("canonical_write", false)'
check U41_mutation_none contains "$MAIN" '.put("state_mutation_mode", "NONE")'
check U42_truth_none contains "$MAIN" '.put("truth_winner", "NONE")'
check U43_answer_token contains "$MAIN" 'NEXUS_EXECUTION_PROOF_006_OK'
check U44_no_chrome_runtime bash -c "! grep -Fq 'chrome.runtime' '$CHAT' '$CLAUDE'"
check U45_no_add_js_interface bash -c "! grep -R -Fq 'addJavascriptInterface' '$ROOT/app/src/main/java' '$CHAT' '$CLAUDE'"
check U46_no_webview_debug contains "$MAIN" 'WebView.setWebContentsDebuggingEnabled(false)'
check U47_node_syntax node --check "$CHAT"

printf 'EXECUTION_PROOF_006_UIRETRY1_STATIC_RESULT pass=%d fail=%d\n' "$PASS" "$FAIL"
test "$PASS" -eq 47
test "$FAIL" -eq 0
