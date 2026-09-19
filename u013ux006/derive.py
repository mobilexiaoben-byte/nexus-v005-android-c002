from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
subprocess.run([sys.executable, str(repo / 'u013ux005' / 'derive.py'), str(repo), str(work)], check=True)

p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared005"', 'applicationId = "nexus.android.u013.shared006"')
s = s.replace('versionCode = 50', 'versionCode = 51')
s = s.replace('versionName = "0.0.50-u013-android-ux-shared005-llm-first"', 'versionName = "0.0.51-u013-android-ux-shared006-real-prompt"')
assert 'nexus.android.u013.shared006' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

old = '    private var lastAuthState: String? = null\n'
assert s.count(old) == 1
s = s.replace(old, old + '    private var lastProviderOrigin: String? = null\n    private var activeUserQuestion: String? = null\n')

old = '''            productRunRequested = true
            if (currentHeadline.startsWith("AUTH REQUIRED")) {
'''
new = '''            val userQuestion = productPrompt.text.toString().trim()
            if (userQuestion.isBlank()) {
                productState.text = "Saisissez une question ou une situation"
                return@setOnClickListener
            }
            productRunRequested = true
            activeUserQuestion = userQuestion
            if (currentHeadline.startsWith("AUTH REQUIRED")) {
'''
assert s.count(old) == 1
s = s.replace(old, new)

old = '''            } else {
                productState.text = "Analyse en cours…"
                webView.visibility = View.GONE
                if (resultPanel.visibility == View.VISIBLE) {
                    showNexusResult()
                } else {
                    productHome.visibility = View.VISIBLE
                }
            }
        }
'''
new = '''            } else {
                val providerOrigin = lastProviderOrigin
                if (!describePassed || providerOrigin.isNullOrBlank()) {
                    productState.text = "Connexion au LLM en cours…"
                    return@setOnClickListener
                }
                productState.text = "Analyse en cours…"
                resultPanel.visibility = View.GONE
                webView.visibility = View.GONE
                productHome.visibility = View.VISIBLE
                startExecutionProof(providerOrigin)
            }
        }
'''
assert s.count(old) == 1
s = s.replace(old, new)

old = '''        describePassed = true
        recordDiagnostic("DESCRIBE_PASS", origin, "authenticated=true")
        currentHeadline = "DESCRIBE PASS — execution proof starting"
        currentBody = null
        renderStatus()
        startExecutionProof(origin)
'''
new = '''        describePassed = true
        lastProviderOrigin = origin
        recordDiagnostic("DESCRIBE_PASS", origin, "authenticated=true")
        currentHeadline = "DESCRIBE PASS — ChatGPT ready"
        currentBody = null
        renderStatus()
        if (productRunRequested && !activeUserQuestion.isNullOrBlank()) startExecutionProof(origin)
'''
assert s.count(old) == 1
s = s.replace(old, new)

old = '''        val input = ExecutionInput(
            requestId = JOB_ID,
            question = PROOF_QUESTION,
'''
new = '''        val userQuestion = activeUserQuestion?.trim().orEmpty()
        if (userQuestion.isBlank()) {
            block("ANDROID_USER_QUESTION_MISSING")
            return
        }
        val input = ExecutionInput(
            requestId = JOB_ID,
            question = userQuestion,
'''
assert s.count(old) == 1
s = s.replace(old, new)

assert s.count('.put("answer", PROOF_TOKEN)') == 2
s = s.replace('.put("answer", PROOF_TOKEN)', '.put("answer", ANSWER_PLACEHOLDER)', 1)
old = '        if (resultPack.optString("answer") != PROOF_TOKEN) return "ANDROID_RESULT_ANSWER_MISMATCH"\n'
new = '        val answer = resultPack.optString("answer").trim()\n        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"\n        if (answer == ANSWER_PLACEHOLDER) return "ANDROID_RESULT_ANSWER_PLACEHOLDER"\n'
assert s.count(old) == 1
s = s.replace(old, new)
old = '        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")\n'
new = '        val finalAnswer = resultPack.optString("answer").trim()\n        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=${job.jobId};answer_length=${finalAnswer.length}")\n'
assert s.count(old) == 1
s = s.replace(old, new)
assert s.count('.put("answer", PROOF_TOKEN)') == 1
s = s.replace('.put("answer", PROOF_TOKEN)', '.put("answer_present", finalAnswer.isNotBlank()).put("answer_length", finalAnswer.length)', 1)
old = '        const val RESULT_PACK_VERSION = "U013_ANDROID_UX_SHARED_001_V1"\n'
assert s.count(old) == 1
s = s.replace(old, old + '        const val ANSWER_PLACEHOLDER = "__NEXUS_MODEL_ANSWER__"\n')
assert 'question = PROOF_QUESTION' not in s
assert 'question = userQuestion' in s
assert 'startExecutionProof(providerOrigin)' in s
p.write_text(s)

p = work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
s = p.read_text()
s = s.replace('You are executing a NEXUS read-only post-response audit in this authenticated ChatGPT browser session.', 'You are executing a NEXUS read-only user analysis in this authenticated ChatGPT browser session.')
s = s.replace('- Use only the supplied frozen package below.', '- Answer the QUESTION directly using your current model knowledge and the supplied frozen package metadata.')
s = s.replace('- Do NOT rewrite Analysis A.', '- Keep the answer concise, useful, and directly responsive to QUESTION.')
s = s.replace('- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.', '- Preserve the expected Result Pack structure and static fields, but replace expected_result_pack.answer with your substantive answer to QUESTION. Never return the placeholder __NEXUS_MODEL_ANSWER__.')
for token in ['read-only user analysis', 'substantive answer to QUESTION', '__NEXUS_MODEL_ANSWER__']:
    assert token in s
p.write_text(s)

(work / 'U013_BASELINE_LOCK.txt').write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_006\n'
    'INHERITED_DEVICE_VALIDATION=SHARED_005\n'
    'USER_PROMPT_SOURCE=productPrompt\n'
    'EXECUTION_TRIGGER=ANALYSE_BUTTON_ONLY\n'
    'AUTO_PROOF_ON_AUTH=DISABLED\n'
    'RESULT_PACK_ANSWER=DYNAMIC_NONEMPTY\n'
    'STATIC_CORRELATION_AND_AUDIT=VALIDATED\n'
    'EXTERNAL_RESEARCH=false\n'
    'CANONICAL_WRITE=false\n'
    'STATE_MUTATION=NONE\n'
    'ACTIVE_ANDROID_PROVIDER_ADAPTER=ChatGPT_ONLY\n'
    'FACTCHECK_RUNTIME=NOT_CLAIMED\n'
)
