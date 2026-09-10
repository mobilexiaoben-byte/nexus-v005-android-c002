#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root required}"
pass=0
fail=0
check(){
  local name="$1"; shift
  if "$@"; then echo "PASS $name"; pass=$((pass+1)); else echo "FAIL $name"; fail=$((fail+1)); fi
}
contains(){ grep -Fq "$2" "$1"; }
not_contains(){ ! grep -Fq "$2" "$1"; }

MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
CORE="$ROOT/app/src/main/java/nexus/android/c002/core/TransportContract.kt"
BRIDGE="$ROOT/app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
POLICY="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
ZAI="$ROOT/app/src/main/assets/nexus/zai_provider_c002.js"
GEMINI="$ROOT/app/src/main/assets/nexus/gemini_provider_c002.js"
GRADLE="$ROOT/app/build.gradle.kts"
MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"

check app_id contains "$GRADLE" 'applicationId = "nexus.android.c002.zaiexecutionproof001"'
check version_name contains "$GRADLE" 'versionName = "0.0.28-v005-zai-android-proof001"'
check manifest_label contains "$MANIFEST" 'NEXUS ZAI ANDROID PROOF 001'
check zai_asset test -f "$ZAI"
check gemini_asset_preserved test -f "$GEMINI"
check zai_enum contains "$CORE" 'CHATGPT, CLAUDE, GEMINI, ZAI'
check zai_enabled contains "$CORE" 'SelectedProvider.ZAI to ProviderPolicy("ZAI", "ADP-ZAI-GLM-FAMILY", "https://chat.z.ai", true)'
check gemini_enabled_preserved contains "$CORE" 'SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true)'
check bridge_signature contains "$BRIDGE" 'zaiAdapterScript: String'
check bridge_zai_injection contains "$BRIDGE" 'setOf("https://chat.z.ai")'
check bridge_origin contains "$POLICY" '"https://chat.z.ai"'
check navigation_zai contains "$POLICY" 'host == "z.ai" || host.endsWith(".z.ai")'
check navigation_google_auth contains "$POLICY" 'host == "accounts.google.com"'
check main_load_zai contains "$MAIN" 'webView.loadUrl("$ZAI_ORIGIN/")'
check main_selected_zai contains "$MAIN" 'provider = SelectedProvider.ZAI,'
check main_zai_expected contains "$MAIN" '.put("provider", "Z.ai")'
check main_zai_validate contains "$MAIN" 'model.optString("provider") != "Z.ai"'
check main_channel contains "$MAIN" 'ZAI_CHANNEL = "NEXUS_V005_ZAI_001"'
check main_origin contains "$MAIN" 'ZAI_ORIGIN = "https://chat.z.ai"'
check main_contract contains "$MAIN" 'V005-ZAI-ANDROID-PROOF-001'
check main_token contains "$MAIN" 'NEXUS_ZAI_EXECUTION_PROOF_001_OK'
check no_gemini_selected not_contains "$MAIN" 'provider = SelectedProvider.GEMINI,'
check adapter_channel contains "$ZAI" "const CHANNEL='NEXUS_V005_ZAI_001'"
check adapter_status contains "$ZAI" "type:'ZAI_STATUS'"
check adapter_provider_family contains "$ZAI" "envelope.provider_family!=='ZAI'"
check adapter_external_research contains "$ZAI" "envelope.external_research!==false"
check adapter_state_mutation contains "$ZAI" "STATE_MUTATION_FORBIDDEN"
check adapter_composer contains "$ZAI" "document.getElementById('chat-input')"
check adapter_send contains "$ZAI" "'#send-message-button'"
check adapter_response contains "$ZAI" "document.querySelectorAll('.chat-assistant')"
check adapter_submission_proof contains "$ZAI" 'ZAI_PROMPT_SUBMISSION_NOT_ESTABLISHED'
check adapter_prompt_false_positive_guard contains "$ZAI" "raw.includes('FROZEN PACKAGE:')"
check adapter_json_required contains "$ZAI" "required=['result_pack_version','pack_id','comparison_id','model','answer','audit']"
check adapter_result contains "$ZAI" "type:'PROVIDER_RESULT'"
check adapter_ui_origin contains "$ZAI" 'ui_origin:location.origin'
check no_chrome_runtime not_contains "$ZAI" 'chrome.runtime'
check no_provider_api_endpoint not_contains "$ZAI" '/api/chat/completions'
check no_secret_literal not_contains "$ZAI" 'API_KEY'

if command -v node >/dev/null 2>&1; then
  check zai_js_syntax node --check "$ZAI"
fi

echo "ZAI_PROOF001_STATIC_RESULT pass=$pass fail=$fail"
[[ "$fail" -eq 0 ]]
