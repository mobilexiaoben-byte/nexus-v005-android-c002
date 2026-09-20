from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / "app/src/main/assets/nexus"
main = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
layout = root / "app/src/main/res/layout/activity_main.xml"
gradle = root / "app/build.gradle.kts"
lock = root / "RECONCILIATION_LOCK.txt"

# 1) Restore the U013 real-answer contract AFTER Golden provider reconstruction.
provider_files = sorted(assets.glob("*provider*.js"))
assert provider_files, "provider assets missing"
patched_prompt_files = []
for p in provider_files:
    s = p.read_text()
    before = s

    s = s.replace(
        "You are executing a NEXUS read-only post-response audit in this authenticated ChatGPT browser session.",
        "You are executing a NEXUS read-only user analysis in this authenticated ChatGPT browser session."
    )
    s = s.replace(
        "You are executing a NEXUS read-only post-response audit in this authenticated Gemini browser session.",
        "You are executing a NEXUS read-only user analysis in this authenticated Gemini browser session."
    )
    s = s.replace(
        "- Use only the supplied frozen package below.",
        "- Use the supplied frozen package as execution metadata and follow the resolved research policy below."
    )
    s = s.replace(
        "- Do NOT rewrite Analysis A.",
        "- Answer QUESTION directly with a substantive, useful answer."
    )
    s = s.replace(
        "- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.",
        "- Preserve the expected Result Pack structure and correlation/static fields, but replace expected_result_pack.answer with your substantive answer to QUESTION; never return __NEXUS_MODEL_ANSWER__ or a formatting variant of that placeholder. audit.external_research must be a boolean that truthfully reports whether external research was actually used."
    )
    s = s.replace(
        "Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.",
        "Preserve the expected Result Pack structure and correlation/static fields, but replace expected_result_pack.answer with your substantive answer to QUESTION; never return __NEXUS_MODEL_ANSWER__ or a formatting variant of that placeholder. audit.external_research must be a boolean that truthfully reports whether external research was actually used."
    )
    # REQUIRED must mean actual research, not merely permission.
    s = s.replace(
        "- Research policy REQUIRED: perform external research when available and permitted; preserve source traceability.",
        "- Research policy REQUIRED: perform external web research before answering; use available web/search capability, preserve source traceability, and set audit.external_research=true only if research was actually performed."
    )
    s = s.replace(
        "- Research policy REQUIRED: perform the external research required by the job and cite/trace sources as required by source_policy.",
        "- Research policy REQUIRED: perform external web research before answering; use available web/search capability, preserve source traceability, and set audit.external_research=true only if research was actually performed."
    )
    s = s.replace(
        "- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy.",
        "- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy; audit.external_research must truthfully reflect actual use."
    )

    # Golden reconstruction also reintroduced the visible provider diagnostic badge.
    # Hide it from normal UX; technical state remains in Rapport/diagnostics.
    if "badge.style.cssText=[" in s and "'display:none'" not in s[s.index("badge.style.cssText=["):s.index("badge.style.cssText=[")+250]:
        s = s.replace("badge.style.cssText=[", "badge.style.cssText=[\n      'display:none',", 1)

    if s != before:
        p.write_text(s)
        patched_prompt_files.append(p.name)

assert "chatgpt_provider_c002.js" in patched_prompt_files
assert "gemini_provider_c002.js" in patched_prompt_files

# 2) Explicit user web intent => M024 REQUIRED instead of generic OPEN_ANALYSIS/OPTIONAL.
m = main.read_text()
old = '''        val jobType = nexus.android.c002.core.JobType.OPEN_ANALYSIS
        val resolvedResearchPolicy = nexus.android.c002.core.resolveResearchPolicy(jobType)
'''
new = '''        val normalizedResearchIntent = userQuestion.lowercase()
        val explicitWebResearchRequested =
            listOf("recherche web", "recherche internet", "recherche en ligne", "web search", "search the web", "internet research")
                .any { normalizedResearchIntent.contains(it) }
        val jobType = if (explicitWebResearchRequested)
            nexus.android.c002.core.JobType.POPINT_RESEARCH
        else
            nexus.android.c002.core.JobType.OPEN_ANALYSIS
        val resolvedResearchPolicy = nexus.android.c002.core.resolveResearchPolicy(jobType)
'''
assert old in m, "job type routing anchor missing"
m = m.replace(old, new, 1)

# 3) Reject placeholder even when the model wraps it in Markdown or changes separators.
old = '''        val answer = resultPack.optString("answer").trim()
        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"
        if (answer == ANSWER_PLACEHOLDER) return "ANDROID_RESULT_ANSWER_PLACEHOLDER"
'''
new = '''        val answer = resultPack.optString("answer").trim()
        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"
        val normalizedAnswerToken = answer.replace(Regex("[^A-Za-z0-9]"), "").uppercase()
        if (answer == ANSWER_PLACEHOLDER || normalizedAnswerToken == "NEXUSMODELANSWER")
            return "ANDROID_RESULT_ANSWER_PLACEHOLDER"
'''
assert old in m, "answer validation anchor missing"
m = m.replace(old, new, 1)

# Make the expected audit field explicitly a template value, not a false factual claim.
old = '                .put("external_research", false)\n'
assert old in m, "external research expected-result anchor missing"
m = m.replace(old, '                .put("external_research", JSONObject.NULL)\n', 1)

# Visible provider state follows the manual confirmation authority.
old = '        productState.text = "$provider · connecté (confirmé par l’utilisateur)"\n'
assert old in m, "provider confirmation status anchor missing"
m = m.replace(old, '        productState.text = "$provider · session opérationnelle (confirmée)"\n', 1)

main.write_text(m)

# 4) Result page: bound-height, vertically scrollable answer block.
x = layout.read_text()
pattern = re.compile(r'''            <TextView\n                android:id="@\+id/resultSummary"\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="20dp"\n                android:padding="18dp"\n                android:background="#FFFFFF"\n                android:text="[^"]*"\n                android:textColor="#202123"\n                android:textSize="16sp"\n                android:lineSpacingExtra="4dp" />''')
match = pattern.search(x)
assert match, "resultSummary layout anchor missing"
scroll_block = '''            <ScrollView
                android:id="@+id/resultAnswerScroll"
                android:layout_width="match_parent"
                android:layout_height="0dp"
                android:layout_weight="1"
                android:layout_marginTop="20dp"
                android:fillViewport="false"
                android:overScrollMode="ifContentScrolls"
                android:background="#FFFFFF">

                <TextView
                    android:id="@+id/resultSummary"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:minHeight="180dp"
                    android:padding="18dp"
                    android:text="Résultat en attente…"
                    android:textColor="#202123"
                    android:textSize="16sp"
                    android:lineSpacingExtra="4dp"
                    android:textIsSelectable="true" />
            </ScrollView>'''
x = x[:match.start()] + scroll_block + x[match.end():]
layout.write_text(x)

# Candidate identity only.
b = gradle.read_text()
assert "versionCode = 77" in b
assert 'versionName = "0.0.77-v007-golden-recovery005-gemini-manual-auth-fix"' in b
b = b.replace("versionCode = 77", "versionCode = 78", 1)
b = b.replace(
    'versionName = "0.0.77-v007-golden-recovery005-gemini-manual-auth-fix"',
    'versionName = "0.0.78-v007-golden-recovery006-unified-result-web-ui-fix"',
    1
)
gradle.write_text(b)

lock.write_text(lock.read_text() +
    "GOLDEN_RECOVERY006_REAL_ANSWER=RESTORED_AFTER_GOLDEN_PROVIDER_COPY\n"
    "GOLDEN_RECOVERY006_PLACEHOLDER_VARIANTS=REJECTED\n"
    "GOLDEN_RECOVERY006_EXPLICIT_WEB_INTENT=POPINT_RESEARCH_REQUIRED\n"
    "GOLDEN_RECOVERY006_EXPECTED_EXTERNAL_RESEARCH=TEMPLATE_NULL_ACTUAL_BOOLEAN_REQUIRED\n"
    "GOLDEN_RECOVERY006_RESULT_UI=SCROLLABLE_BOUNDED_ANSWER_BLOCK\n"
    "GOLDEN_RECOVERY006_PROVIDER_DEBUG_BADGE=HIDDEN_NORMAL_UX\n"
    "GOLDEN_RECOVERY006_MANUAL_CONFIRMATION_STATUS=SESSION_OPERATIONAL\n"
    "GOLDEN_RECOVERY006_TRANSPORT_PATHS=PRESERVED\n"
    "GOLDEN_RECOVERY006_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Fail closed on the exact requested corrections.
out = main.read_text()
lay = layout.read_text()
chat = (assets / "chatgpt_provider_c002.js").read_text()
gem = (assets / "gemini_provider_c002.js").read_text()
assert "POPINT_RESEARCH" in out and "explicitWebResearchRequested" in out
assert 'normalizedAnswerToken == "NEXUSMODELANSWER"' in out
assert '.put("external_research", JSONObject.NULL)' in out
assert "session opérationnelle (confirmée)" in out
assert 'android:id="@+id/resultAnswerScroll"' in lay
assert 'android:layout_weight="1"' in lay
assert 'android:textIsSelectable="true"' in lay
for js in [chat, gem]:
    assert "substantive answer to QUESTION" in js
    assert "never return __NEXUS_MODEL_ANSWER__" in js
    assert "audit.external_research must be a boolean" in js
    assert "'display:none'" in js
