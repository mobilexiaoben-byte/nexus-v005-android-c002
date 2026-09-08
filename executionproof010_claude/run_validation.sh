#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root required}"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
CLAUDE="$ROOT/app/src/main/assets/nexus/claude_provider_c002.js"
CHATGPT="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
POLICY="$ROOT/app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"

pass=0
fail=0
check(){
  local label="$1"; shift
  if "$@"; then echo "PASS $label"; pass=$((pass+1)); else echo "FAIL $label"; fail=$((fail+1)); fi
}
contains(){ grep -Fq -- "$2" "$1"; }
not_contains(){ ! grep -Fq -- "$2" "$1"; }

check claude_adapter_present test -s "$CLAUDE"
check chatgpt_adapter_present test -s "$CHATGPT"
check claude_origin contains "$MAIN" 'const val CLAUDE_ORIGIN = "https://claude.ai"'
check claude_selected contains "$MAIN" 'provider = SelectedProvider.CLAUDE,'
check anthropic_expected contains "$MAIN" '.put("provider", "Anthropic")'
check anthropic_validated contains "$MAIN" 'model.optString("provider") != "Anthropic"'
check claude_token contains "$MAIN" 'NEXUS_CLAUDE_EXECUTION_PROOF_010_OK'
check claude_contract contains "$MAIN" 'V005-C002-CLAUDE-EXECUTION-PROOF-010'
check claude_channel_bound contains "$MAIN" 'CLAUDE_CHANNEL_BOUND'
check channel_unbound_fail_closed contains "$MAIN" 'ANDROID_BRIDGE_CHANNEL_UNBOUND'
check origin_mismatch_fail_closed contains "$MAIN" 'ANDROID_BRIDGE_ORIGIN_MISMATCH'
check provider_ack contains "$MAIN" 'type == "PROVIDER_ACK"'
check provider_progress contains "$MAIN" 'type == "PROVIDER_PROGRESS"'
check provider_result contains "$MAIN" 'type == "PROVIDER_RESULT"'
check no_chatgpt_selected not_contains "$MAIN" 'SelectedProvider.CHATGPT'
check no_chatgpt_origin_symbol not_contains "$MAIN" 'CHATGPT_ORIGIN'
check no_chatgpt_channel_symbol not_contains "$MAIN" 'CHATGPT_CHANNEL'
check external_research_false contains "$MAIN" '.put("external_research", false)'
check canonical_write_false contains "$MAIN" '.put("canonical_write", false)'
check state_mutation_none contains "$MAIN" '.put("state_mutation_mode", "NONE")'
check truth_winner_none contains "$MAIN" '.put("truth_winner", "NONE")'
check transport_preserved contains "$MAIN" 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"'
check origin_policy_claude contains "$POLICY" 'host == "claude.ai" || host.endsWith(".claude.ai")'
check origin_policy_anthropic contains "$POLICY" 'host == "anthropic.com" || host.endsWith(".anthropic.com")'
check no_wildcard_auth not_contains "$POLICY" 'accounts.google.*'

# The frozen C002 core must actually expose the Claude enum used by the proof.
CORE_PROVIDER="$ROOT/app/src/main/java/nexus/android/c002/core/TransportModels.kt"
if [[ ! -f "$CORE_PROVIDER" ]]; then
  CORE_PROVIDER="$(grep -RIl 'enum class SelectedProvider' "$ROOT/app/src/main/java/nexus/android/c002/core" | head -n1 || true)"
fi
check selected_provider_source test -n "$CORE_PROVIDER"
if [[ -n "$CORE_PROVIDER" ]]; then
  check selected_provider_claude contains "$CORE_PROVIDER" 'CLAUDE'
fi

echo "CLAUDE_EXECUTION_PROOF_010_STATIC_RESULT pass=$pass fail=$fail"
[[ "$fail" -eq 0 ]]
