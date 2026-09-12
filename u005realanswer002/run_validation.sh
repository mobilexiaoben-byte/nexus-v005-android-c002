#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?android project root required}"
MAIN="$ROOT/app/src/main/java/nexus/android/c002/MainActivity.kt"
JS="$ROOT/app/src/main/assets/nexus/chatgpt_provider_c002.js"
pass=0
fail=0
check(){
  local name="$1"; shift
  if "$@"; then echo "PASS $name"; pass=$((pass+1)); else echo "FAIL $name"; fail=$((fail+1)); fi
}
check dynamic_answer_contract grep -Fq '.put("answer", JSONObject().put("source", "PROVIDER_LIVE_ANSWER_TO_QUESTION"))' "$MAIN"
check dynamic_question grep -Fq 'calcule 17 × 23' "$MAIN"
check question_does_not_disclose_answer bash -c '! grep -F "const val PROOF_QUESTION" "$1" | grep -Fq "391"' _ "$MAIN"
check new_result_pack_version grep -Fq 'U005_ANDROID_REAL_ANSWER_002_V1' "$MAIN"
check new_job_id grep -Fq 'U005-ANDROID-REAL-ANSWER-002-JOB-001' "$MAIN"
check answer_nonempty_gate grep -Fq 'ANDROID_RESULT_ANSWER_EMPTY' "$MAIN"
check legacy_placeholder_rejected grep -Fq 'ANDROID_RESULT_ANSWER_STATIC_PLACEHOLDER' "$MAIN"
check live_marker_gate grep -Fq 'ANDROID_RESULT_ANSWER_MARKER_MISSING' "$MAIN"
check visible_result_uses_provider_answer grep -Fq '.put("answer", resultPack.optString("answer"))' "$MAIN"
check no_old_exact_answer_gate bash -c '! grep -Fq "if (resultPack.optString(\"answer\") != PROOF_TOKEN)" "$1"' _ "$MAIN"
check prompt_computes_answer grep -Fq 'Compute the answer to QUESTION yourself.' "$JS"
check prompt_answer_is_string grep -Fq 'result_pack.answer MUST be a JSON string containing your direct answer to QUESTION.' "$JS"
check no_exact_expected_pack_copy bash -c '! grep -Fq "Return exactly frozen_package.output_contract.expected_result_pack" "$1"' _ "$JS"
check complete_json_parser grep -Fq "const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];" "$JS"
check javascript_syntax node --check "$JS"
echo "U005_REAL_ANSWER_002_STATIC_RESULT pass=$pass fail=$fail"
[[ "$fail" -eq 0 ]]
