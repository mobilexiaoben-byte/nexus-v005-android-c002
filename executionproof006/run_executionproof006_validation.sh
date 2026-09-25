#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
POLICY="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
CHAT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
CONTRACT="$ROOT/app/src/main/java/nexus/android/c002/core/TransportContract.kt"
LAYOUT="$ROOT/app/src/main/res/layout/activity_main.xml"
PASS=0; FAIL=0
check(){ local id="$1"; shift; if "$@"; then echo "PASS $id"; PASS=$((PASS+1)); else echo "FAIL $id"; FAIL=$((FAIL+1)); fi; }
check_text(){ grep -Fq "$2" "$1"; }
check E01_package check_text "$ROOT/app/build.gradle.kts" 'applicationId = "nexus.android.c002.executionproof006"'
check E02_version check_text "$ROOT/app/build.gradle.kts" 'versionCode = 7'
check E03_label check_text "$ROOT/app/src/main/AndroidManifest.xml" 'NEXUS C002 EXECUTION PROOF 006'
check E04_profile check_text "$MAIN" 'nexus_provider_profile_c002_executionproof006'
check E05_describe_gate check_text "$MAIN" 'describePassed = true'
check E06_execute_job check_text "$MAIN" '.put("type", "EXECUTE_JOB")'
check E07_execute_after_describe python3 - "$MAIN" <<'PY'
import sys
s=open(sys.argv[1]).read()
assert s.index('describePassed = true') < s.index('startExecutionProof(origin)') < s.index('.put("type", "EXECUTE_JOB")')
PY
check E08_one_provider check_text "$MAIN" 'provider = SelectedProvider.CHATGPT'
check E09_external_false check_text "$MAIN" '.put("external_research", false)'
check E10_canonical_none check_text "$MAIN" '.put("canonical_rights", "NONE")'
check E11_mutation_none check_text "$MAIN" '.put("state_mutation_mode", "NONE")'
check E12_truth_none check_text "$MAIN" '.put("truth_winner", "NONE")'
check E13_ack_gate check_text "$MAIN" 'RuntimeGate.validateAck'
check E14_ack_timeout check_text "$MAIN" 'ANDROID_ACK_TIMEOUT'
check E15_terminal_timeout check_text "$MAIN" 'ANDROID_TERMINAL_TIMEOUT'
check E16_terminal_correlation check_text "$MAIN" 'ANDROID_TERMINAL_CORRELATION_MISMATCH'
check E17_result_pack_exact check_text "$MAIN" 'ANDROID_RESULT_PACK_ID_MISMATCH'
check E18_answer_exact check_text "$MAIN" 'NEXUS_EXECUTION_PROOF_006_OK'
check E19_receipt_validation check_text "$MAIN" 'engine.validateReceipt(job, receipt)'
check E20_transport_provenance check_text "$MAIN" 'ANDROID_WEBVIEW_CHROMIUM_BRIDGE'
check E21_provider_provenance check_text "$MAIN" 'ProviderMetadata(job.providerFamily, modelRef)'
check E22_no_debug check_text "$MAIN" 'WebView.setWebContentsDebuggingEnabled(false)'
check E23_google_exact check_text "$POLICY" 'host == "accounts.google.com"'
check E24_youtube_exact check_text "$POLICY" 'host == "accounts.youtube.com"'
check E25_no_google_wildcard bash -c "! grep -Fq 'endsWith(\".google.com\")' '$POLICY'"
check E26_no_youtube_wildcard bash -c "! grep -Fq 'endsWith(\".youtube.com\")' '$POLICY'"
check E27_bridge_origins_no_auth_hosts bash -c "python3 - '$POLICY' <<'PY'
import sys
s=open(sys.argv[1]).read(); bridge=s.split('fun isBridgeOriginAllowed',1)[0]
assert 'google' not in bridge and 'youtube' not in bridge
PY"
check E28_claude_unchanged bash -c "cd '$ROOT' && echo 'f1dc78cdbadcc252a529c2db86b15ac42a92f0f2c132181cd1072bc24b131366  app/src/main/assets/nexus/claude_provider_c002.js' | sha256sum -c - >/dev/null"
check E29_bridge_unchanged bash -c "cd '$ROOT' && echo 'a842eb5d15d23b0ace09674585cefbfba2a753c155eeb5b0c0df6aaf9324275a  app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt' | sha256sum -c - >/dev/null"
check E30_core_contract_unchanged bash -c "cd '$ROOT' && echo '408487cffd660e5446c6362e272dd04395c70a575048fa1320c02819845b2a85  app/src/main/java/nexus/android/c002/core/TransportContract.kt' | sha256sum -c - >/dev/null"
check E31_sticky_auth check_text "$CHAT" 'LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE'
check E32_sticky_auth_set check_text "$CHAT" "lastStableAuthState='AUTHENTICATED'"
check E33_explicit_unauth_downgrade check_text "$CHAT" "lastStableAuthState='UNAUTHENTICATED'"
check E34_exact_output_instruction check_text "$CHAT" 'Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.'
check E35_provider_result check_text "$CHAT" "type:'PROVIDER_RESULT'"
check E36_provider_ack check_text "$CHAT" "type:'PROVIDER_ACK'"
check E37_no_chrome_runtime bash -c "! grep -Fq 'chrome.runtime' '$CHAT' '$CLAUDE'"
check E38_no_add_js_interface bash -c "! grep -R -Fq 'addJavascriptInterface' '$ROOT/app/src/main/java' '$CHAT' '$CLAUDE'"
check E39_forbidden_field_scan check_text "$MAIN" 'collectForbiddenKeys(resultPack)'
check E40_no_web_research_prompt check_text "$MAIN" 'No web research'
check E41_terminal_stop check_text "$MAIN" 'EXECUTION PROOF PASS — STOP GATE'
check E42_single_job_guard check_text "$MAIN" 'if (!describePassed || executionStarted || proofStopped) return'
check E43_compact_ui check_text "$LAYOUT" 'android:maxLines="2"'
check E44_https_only check_text "$POLICY" 'if (!uri.scheme.equals("https", ignoreCase = true)) return false'
node --check "$CHAT"
node --check "$CLAUDE"
printf 'EXECUTION_PROOF_006_STATIC_RESULT pass=%d fail=%d\n' "$PASS" "$FAIL"
test "$FAIL" -eq 0
