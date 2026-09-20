from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / "app/src/main/assets/nexus"
main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
gradle = root / "app/build.gradle.kts"
lock = root / "RECONCILIATION_LOCK.txt"

provider_paths = sorted(assets.glob("*provider*.js"))
assert provider_paths, "provider assets missing"

old_literal = "- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response."
new_literal = "- Use frozen_package.output_contract.expected_result_pack as the structural template. Replace answer with a substantive response to QUESTION; never return __NEXUS_MODEL_ANSWER__. Preserve correlation/static fields. Set audit.external_research to true only if external research was actually used, otherwise false."

for p in provider_paths:
    s = p.read_text()
    if old_literal in s:
        s = s.replace(old_literal, new_literal)
    s = s.replace(
        "Preserve the expected Result Pack structure and static fields, but replace expected_result_pack.answer with your substantive answer to QUESTION.",
        "Preserve the expected Result Pack structure and static fields, except audit.external_research must truthfully report actual external research use; replace expected_result_pack.answer with your substantive answer to QUESTION. Never return __NEXUS_MODEL_ANSWER__."
    )
    s = s.replace(
        "Preserve expected Result Pack static fields; replace answer with your substantive answer.",
        "Preserve expected Result Pack static fields except audit.external_research, which must truthfully report actual external research use; replace answer with your substantive answer. Never return __NEXUS_MODEL_ANSWER__."
    )
    p.write_text(s)

chat = assets / "chatgpt_provider_c002.js"
gem = assets / "gemini_provider_c002.js"

for p in [chat, gem]:
    s = p.read_text()
    assert "let running=false;" in s, f"{p.name}: running anchor missing"
    if "userConfirmedSticky" not in s:
        s = s.replace("let running=false;", "let running=false; let userConfirmedSticky=false;", 1)
    confirmed = "      const userConfirmed=(envelope.user_confirmed_connected===true);\n"
    assert confirmed in s, f"{p.name}: manual confirmation anchor missing"
    if "userConfirmedSticky=userConfirmedSticky||userConfirmed;" not in s:
        s = s.replace(confirmed, confirmed + "      userConfirmedSticky=userConfirmedSticky||userConfirmed;\n", 1)

    if p == chat:
        old = """  async function publishStatus(){
    const s=detectAuth();
    if(!running) show('CHATGPT AUTH: '+s.state);
    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
  }
"""
        new = """  async function publishStatus(){
    const observed=detectAuth();
    const s=userConfirmedSticky
      ? {...observed,state:'AUTHENTICATED',reason:'USER_CONFIRMED_CONNECTED__'+String(observed.state||'UNKNOWN')}
      : observed;
    if(!running) show('CHATGPT AUTH: '+s.state);
    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
  }
"""
    else:
        old = """  async function publishStatus(){
    const s=detectAuth();
    if(!running) show('AUTH: '+s.state+' — '+s.reason);
    try{ await nativeSend({channel:CHANNEL,type:'GEMINI_STATUS',status:s}); }catch(_){}
  }
"""
        new = """  async function publishStatus(){
    const observed=detectAuth();
    const s=userConfirmedSticky
      ? {...observed,state:'AUTHENTICATED',reason:'USER_CONFIRMED_CONNECTED__'+String(observed.state||'UNKNOWN')}
      : observed;
    if(!running) show('AUTH: '+s.state+' — '+s.reason);
    try{ await nativeSend({channel:CHANNEL,type:'GEMINI_STATUS',status:s}); }catch(_){}
  }
"""
    assert old in s, f"{p.name}: publishStatus anchor missing"
    s = s.replace(old, new, 1)
    p.write_text(s)

m = main_path.read_text()

old_jobtype = "        val jobType = nexus.android.c002.core.JobType.OPEN_ANALYSIS\n"
new_jobtype = """        val explicitResearchRequested = Regex(
            "(?i)\\\\b(recherche\\\\s+web|recherche\\\\s+internet|chercher\\\\s+sur\\\\s+le\\\\s+web|search\\\\s+the\\\\s+web|web\\\\s+search|internet\\\\s+research)\\\\b"
        ).containsMatchIn(userQuestion)
        val jobType = if (explicitResearchRequested)
            nexus.android.c002.core.JobType.POPINT_RESEARCH
        else
            nexus.android.c002.core.JobType.OPEN_ANALYSIS
"""
assert m.count(old_jobtype) == 1, "jobType OPEN_ANALYSIS anchor missing/ambiguous"
m = m.replace(old_jobtype, new_jobtype, 1)

expected_anchor = '.put("external_research", false)'
idx = m.find("val expectedResult = JSONObject()")
assert idx >= 0, "expectedResult anchor missing"
next_idx = m.find("val frozenPackage", idx)
assert next_idx > idx, "frozenPackage anchor missing"
block = m[idx:next_idx]
assert block.count(expected_anchor) == 1, "expectedResult external_research anchor missing/ambiguous"
block = block.replace(
    expected_anchor,
    '.put("external_research", job.researchPolicy == nexus.android.c002.core.ResearchPolicy.REQUIRED)',
    1
)
m = m[:idx] + block + m[next_idx:]

old_validation = """        val answer = resultPack.optString("answer").trim()
        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"
        if (answer == ANSWER_PLACEHOLDER) return "ANDROID_RESULT_ANSWER_PLACEHOLDER"
"""
new_validation = """        val answer = resultPack.optString("answer").trim()
        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"
        val normalizedAnswer = answer.replace(Regex("[*_`\\\\s]"), "")
        val normalizedPlaceholder = ANSWER_PLACEHOLDER.replace(Regex("[*_`\\\\s]"), "")
        if (normalizedAnswer.equals(normalizedPlaceholder, ignoreCase = true)) return "ANDROID_RESULT_ANSWER_PLACEHOLDER"
"""
assert old_validation in m, "answer validation anchor missing"
m = m.replace(old_validation, new_validation, 1)

bind = "        resultSummary = findViewById(R.id.resultSummary)\n"
scroll = """        resultSummary = findViewById(R.id.resultSummary)
        resultSummary.movementMethod = android.text.method.ScrollingMovementMethod.getInstance()
        resultSummary.isVerticalScrollBarEnabled = true
        resultSummary.overScrollMode = View.OVER_SCROLL_IF_CONTENT_SCROLLS
        resultSummary.maxHeight = (420 * resources.displayMetrics.density).toInt()
        resultSummary.minHeight = (180 * resources.displayMetrics.density).toInt()
"""
assert m.count(bind) == 1, "resultSummary binding anchor missing/ambiguous"
m = m.replace(bind, scroll, 1)

old_footer = '            append("\\n\\nValidé par NEXUS · fournisseur en arrière-plan")\n'
new_footer = '            append("\\n\\nValidé par NEXUS · ").append(selectedProvider ?: "LLM")\n'
assert old_footer in m, "validated-result footer anchor missing"
m = m.replace(old_footer, new_footer, 1)

main_path.write_text(m)

g = gradle.read_text()
assert "versionCode = 77" in g
assert 'versionName = "0.0.77-v007-golden-recovery005-gemini-manual-auth-fix"' in g
g = g.replace("versionCode = 77", "versionCode = 78", 1)
g = g.replace(
    'versionName = "0.0.77-v007-golden-recovery005-gemini-manual-auth-fix"',
    'versionName = "0.0.78-v007-golden-recovery006-shared-pipeline-fix"',
    1
)
gradle.write_text(g)

lock.write_text(lock.read_text() +
    "GOLDEN_RECOVERY006_SCOPE=SHARED_ANDROID_PIPELINE\n"
    "GOLDEN_RECOVERY006_RESULT_ANSWER=SUBSTANTIVE_DYNAMIC_PLACEHOLDER_REJECTED\n"
    "GOLDEN_RECOVERY006_WEB_POLICY=OPEN_ANALYSIS_OPTIONAL_EXPLICIT_WEB_REQUEST_REQUIRED\n"
    "GOLDEN_RECOVERY006_RESULT_UI=SCROLLABLE_180_420DP\n"
    "GOLDEN_RECOVERY006_PROVIDER_STATUS=MANUAL_CONFIRMATION_STICKY_AFTER_EXECUTION\n"
    "GOLDEN_RECOVERY006_CHATGPT_TRANSPORT=PRESERVED\n"
    "GOLDEN_RECOVERY006_GEMINI_RECOVERY005_AUTH=PRESERVED\n"
    "GOLDEN_RECOVERY006_ZAI_TRANSPORT=PRESERVED\n"
    "GOLDEN_RECOVERY006_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

out = main_path.read_text()
assert "POPINT_RESEARCH" in out
assert "explicitResearchRequested" in out
assert "ANDROID_RESULT_ANSWER_PLACEHOLDER" in out
assert "ScrollingMovementMethod.getInstance()" in out
assert 'append(selectedProvider ?: "LLM")' in out
for p in provider_paths:
    js = p.read_text()
    assert old_literal not in js, p.name
for p in [chat, gem]:
    js = p.read_text()
    assert "userConfirmedSticky" in js, p.name
    assert "USER_CONFIRMED_CONNECTED__" in js, p.name
