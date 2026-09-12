from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: derive.py <android-project-root>')
root = Path(sys.argv[1])
main = root / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
js = root / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, got {count}')
    return text.replace(old, new, 1)

s = main.read_text()
s = replace_once(
    s,
    '.put("answer", PROOF_TOKEN)\n            .put("audit", JSONObject()',
    '.put("answer", JSONObject().put("source", "PROVIDER_LIVE_ANSWER_TO_QUESTION"))\n            .put("audit", JSONObject()',
    'expected_result_answer_contract',
)
s = replace_once(
    s,
    'recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")',
    'recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer_length=${resultPack.optString("answer").length};marker_present=${resultPack.optString("answer").contains(PROOF_EXPECTED_MARKER)}")',
    'terminal_receipt_dynamic_answer',
)
s = replace_once(
    s,
    '.put("contract", "U004-ANDROID-UX-SHELL-004")',
    '.put("contract", "U005-ANDROID-REAL-ANSWER-002")',
    'contract_id',
)
s = replace_once(
    s,
    '.put("answer", PROOF_TOKEN)\n            .put("external_research", false)',
    '.put("answer", resultPack.optString("answer"))\n            .put("external_research", false)',
    'current_body_dynamic_answer',
)
s = replace_once(
    s,
    'if (resultPack.optString("answer") != PROOF_TOKEN) return "ANDROID_RESULT_ANSWER_MISMATCH"',
    '''val answer = resultPack.optString("answer").trim()\n        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"\n        if (answer == LEGACY_PROOF_TOKEN) return "ANDROID_RESULT_ANSWER_STATIC_PLACEHOLDER"\n        if (!answer.contains(PROOF_EXPECTED_MARKER)) return "ANDROID_RESULT_ANSWER_MARKER_MISSING"\n        if (answer.length > 2000) return "ANDROID_RESULT_ANSWER_TOO_LONG"''',
    'dynamic_answer_validation',
)
s = replace_once(
    s,
    'const val BRIDGE_RUN_ID = "U004-ANDROID-UX-SHELL-004-BRIDGE-001"\n        const val JOB_ID = "U004-ANDROID-UX-SHELL-004-JOB-001"\n        const val COMPARISON_ID = "U004-ANDROID-UX-SHELL-004-COMP-001"\n        const val RESULT_PACK_VERSION = "U004_ANDROID_UX_SHELL_004_V1"\n        const val PROOF_TOKEN = "Le résultat NEXUS utile est affiché directement dans l\'application Android après validation."',
    'const val BRIDGE_RUN_ID = "U005-ANDROID-REAL-ANSWER-002-BRIDGE-001"\n        const val JOB_ID = "U005-ANDROID-REAL-ANSWER-002-JOB-001"\n        const val COMPARISON_ID = "U005-ANDROID-REAL-ANSWER-002-COMP-001"\n        const val RESULT_PACK_VERSION = "U005_ANDROID_REAL_ANSWER_002_V1"\n        const val LEGACY_PROOF_TOKEN = "Le résultat NEXUS utile est affiché directement dans l\'application Android après validation."\n        const val PROOF_EXPECTED_MARKER = "391"',
    'candidate_ids_and_markers',
)
s = replace_once(
    s,
    'const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android transport proof. The answer field must be Le résultat NEXUS utile est affiché directement dans l\'application Android après validation.."\n        const val PROOF_HANDOFF = "Read-only U-004 Android UX transport-regression proof. Use only the frozen package. No web research, no canonical write, no state mutation."',
    'const val PROOF_QUESTION = "Sans utiliser le web, calcule 17 × 23. Réponds en français en une phrase courte et inclus le résultat numérique en chiffres."\n        const val PROOF_HANDOFF = "Read-only U-005 Android live-answer round-trip proof. Generate the provider answer from the question; no web research, no canonical write, no state mutation."',
    'live_question_and_handoff',
)
main.write_text(s)

j = js.read_text()
j = replace_once(
    j,
    "      '- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.',\n      '- For result_pack.model.provider use \"OpenAI\".',",
    "      '- Build one Result Pack from frozen_package.output_contract.expected_result_pack.',\n      '- Copy result_pack_version, pack_id, comparison_id, model, and audit exactly from that contract.',\n      '- expected_result_pack.answer is an answer-source contract, not an answer value.',\n      '- Compute the answer to QUESTION yourself. Do not copy the answer-source contract into answer.',\n      '- result_pack.answer MUST be a JSON string containing your direct answer to QUESTION.',\n      '- For result_pack.model.provider use \"OpenAI\".',",
    'provider_dynamic_answer_prompt',
)
js.write_text(j)
print('U005_REAL_ANSWER_002_DERIVE_PASS')
