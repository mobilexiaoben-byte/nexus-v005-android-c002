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
GEMINI="$ROOT/app/src/main/assets/nexus/gemini_provider_c002.js"
GRADLE="$ROOT/app/build.gradle.kts"
MANIFEST="$ROOT/app/src/main/AndroidManifest.xml"

check app_id contains "$GRADLE" 'applicationId = "nexus.android.c002.geminiexecutionproof001"'
check version_name contains "$GRADLE" 'versionName = "0.0.27-v004-gemini-android-proof001"'
check manifest_label contains "$MANIFEST" 'NEXUS V004 GEMINI ANDROID PROOF 001'
check gemini_asset test -f "$GEMINI"
check gemini_enabled contains "$CORE" 'SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true)'
check gemini_disabled_removed not_contains "$CORE" 'SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", false)'
check bridge_signature contains "$BRIDGE" 'geminiAdapterScript: String'
check bridge_gemini_injection contains "$BRIDGE" 'setOf("https://gemini.google.com")'
check bridge_origin contains "$POLICY" '"https://gemini.google.com"'
check navigation_gemini contains "$POLICY" 'host == "gemini.google.com"'
check navigation_google_auth contains "$POLICY" 'host == "accounts.google.com"'
check main_load_gemini contains "$MAIN" 'webView.loadUrl("$GEMINI_ORIGIN/")'
check main_selected_gemini contains "$MAIN" 'provider = SelectedProvider.GEMINI,'
check main_google_expected contains "$MAIN" '.put("provider", "Google")'
check main_google_validate contains "$MAIN" 'model.optString("provider") != "Google"'
check main_channel contains "$MAIN" 'GEMINI_CHANNEL = "NEXUS_V004_GEMINI_001"'
check main_origin contains "$MAIN" 'GEMINI_ORIGIN = "https://gemini.google.com"'
check main_contract contains "$MAIN" 'V004-GEMINI-ANDROID-PROOF-001'
check main_token contains "$MAIN" 'NEXUS_GEMINI_EXECUTION_PROOF_001_OK'
check no_chatgpt_selected not_contains "$MAIN" 'SelectedProvider.CHATGPT'
check adapter_channel contains "$GEMINI" "const CHANNEL='NEXUS_V004_GEMINI_001'"
check adapter_status contains "$GEMINI" "type:'GEMINI_STATUS'"
check adapter_provider_family contains "$GEMINI" "envelope.provider_family!=='GOOGLE'"
check adapter_external_research contains "$GEMINI" "envelope.external_research!==false"
check adapter_state_mutation contains "$GEMINI" "STATE_MUTATION_FORBIDDEN"
check adapter_composer contains "$GEMINI" 'rich-textarea [contenteditable="true"]'
check adapter_send contains "$GEMINI" 'button.send-button'
check adapter_response contains "$GEMINI" 'model-response'
check adapter_submission_proof contains "$GEMINI" 'GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED'
check adapter_json_required contains "$GEMINI" "required=['result_pack_version','pack_id','comparison_id','model','answer','audit']"
check adapter_result contains "$GEMINI" "type:'PROVIDER_RESULT'"
check adapter_ui_origin contains "$GEMINI" 'ui_origin:location.origin'
check no_chrome_runtime not_contains "$GEMINI" 'chrome.runtime'
check no_api_endpoint not_contains "$GEMINI" 'generativelanguage.googleapis.com'
check no_secret_literal not_contains "$GEMINI" 'API_KEY'

if command -v node >/dev/null 2>&1; then
  check gemini_js_syntax node --check "$GEMINI"
fi

echo "GEMINI_PROOF001_STATIC_RESULT pass=$pass fail=$fail"
[[ "$fail" -eq 0 ]]
