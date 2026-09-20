from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / "app/src/main/assets/nexus"
main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
layout_path = root / "app/src/main/res/layout/activity_main.xml"
gradle = root / "app/build.gradle.kts"
lock = root / "RECONCILIATION_LOCK.txt"

def hide_badge(s):
    if "badge.style.cssText=[" in s:
        pos=s.index("badge.style.cssText=[")
        chunk=s[pos:pos+260]
        if "'display:none'" not in chunk and '"display:none"' not in chunk:
            s=s.replace("badge.style.cssText=[","badge.style.cssText=[\n      'display:none',",1)
    if "badge.style.cssText='position:fixed" in s:
        s=s.replace("badge.style.cssText='position:fixed","badge.style.cssText='display:none;position:fixed",1)
    if 'badge.style.cssText="position:fixed' in s:
        s=s.replace('badge.style.cssText="position:fixed','badge.style.cssText="display:none;position:fixed',1)
    return s

def repair_prompt(s, provider_name, model_label):
    s=s.replace("read-only post-response audit","read-only user analysis")
    s=s.replace("- Use only the supplied frozen package below.",
                "- Use the supplied frozen package as execution metadata and follow the resolved research policy below.")
    s=s.replace("- Do NOT rewrite Analysis A.",
                "- Answer QUESTION directly with a substantive, useful answer.")
    old="- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response."
    new="- Preserve the expected Result Pack structure and correlation/static fields, but replace expected_result_pack.answer with a substantive answer to QUESTION; never return __NEXUS_MODEL_ANSWER__ or a formatting variant. audit.external_research must truthfully report actual external research use."
    s=s.replace(old,new)
    s=s.replace("Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.",
                "Preserve the expected Result Pack structure and correlation/static fields, but replace expected_result_pack.answer with a substantive answer to QUESTION; never return __NEXUS_MODEL_ANSWER__ or a formatting variant. audit.external_research must truthfully report actual external research use.")
    s=s.replace("- Research policy REQUIRED: perform external research when available and permitted; preserve source traceability.",
                "- Research policy REQUIRED: perform external web research before answering; preserve source traceability; set audit.external_research=true only if research was actually performed.")
    s=s.replace("- Research policy REQUIRED: perform the external research required by the job and cite/trace sources as required by source_policy.",
                "- Research policy REQUIRED: perform external web research before answering; preserve source traceability; set audit.external_research=true only if research was actually performed.")
    s=s.replace("- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy.",
                "- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy; audit.external_research must truthfully reflect actual use.")
    if provider_name=="Google":
        s=s.replace('ChatGPT UI session — exact backend model not exposed by bridge',
                    'Gemini UI session — exact backend model not exposed by bridge')
    return hide_badge(s)

provider_files=sorted(assets.glob("*provider*.js"))
assert provider_files, "provider assets missing"

# Provider prompt / badge repairs.
for p in provider_files:
    s=p.read_text()
    low=p.name.lower()
    provider="Google" if "gemini" in low else ("OpenAI" if "chatgpt" in low else "")
    s=repair_prompt(s,provider,"")
    p.write_text(s)

# Gemini: explicit manual confirmation may satisfy auth only with a real visible composer.
gem=assets/"gemini_provider_c002.js"
if gem.exists():
    g=gem.read_text()
    old="""      const auth=detectAuth();
      if(auth.state!=='AUTHENTICATED') throw new Error('GEMINI_NOT_AUTHENTICATED:'+auth.state);
"""
    if old in g:
        new="""      const observedAuth=detectAuth();
      const userConfirmed=(envelope.user_confirmed_connected===true);
      const composerAtDispatch=findComposer();
      const auth=(userConfirmed&&!!composerAtDispatch)
        ? {...observedAuth,state:'AUTHENTICATED',reason:'USER_CONFIRMED_CONNECTED_WITH_VISIBLE_COMPOSER__'+String(observedAuth.state||'UNKNOWN')}
        : observedAuth;
      if(auth.state!=='AUTHENTICATED') throw new Error('GEMINI_NOT_AUTHENTICATED:'+auth.state);
"""
        g=g.replace(old,new,1)
        g=g.replace("      const composer=findComposer();\n      if(!composer) throw new Error('GEMINI_COMPOSER_NOT_FOUND');",
                    "      const composer=composerAtDispatch||findComposer();\n      if(!composer) throw new Error('GEMINI_COMPOSER_NOT_FOUND');",1)
    gem.write_text(g)

# ChatGPT: keep Golden retry/send path, but allow correlated Result Pack capture
# from a changed assistant block even when ChatGPT reuses DOM nodes.
chat=assets/"chatgpt_provider_c002.js"
if chat.exists():
    c=chat.read_text()
    if "function assistantSnapshot()" in c and "waitForAssistantResult(beforeSnapshot,envelope,80000)" in c:
        # Recovery001 already has text-snapshot capture; extend fallback with correlation scan.
        anchor="      const nodes=assistantNodes();\n      lastNodeCount=nodes.length;\n"
        if anchor in c and "correlatedFallback" not in c:
            insert="""      const nodes=assistantNodes();
      lastNodeCount=nodes.length;
      const correlatedFallback=nodes.slice().reverse().find(el=>{
        const txt=assistantNodeText(el);
        const candidate=parseCompleteResultCandidate(txt,envelope);
        return !!candidate;
      });
"""
            c=c.replace(anchor,insert,1)
            old="""      const changed=nodes.filter(el=>{
        const txt=assistantNodeText(el);
        return txt && !beforeSnapshot.has(txt);
      });
"""
            new="""      let changed=nodes.filter(el=>{
        const txt=assistantNodeText(el);
        return txt && !beforeSnapshot.has(txt);
      });
      if(changed.length===0 && correlatedFallback) changed=[correlatedFallback];
"""
            if old in c: c=c.replace(old,new,1)
    chat.write_text(c)

# Claude: do not call a click a successful send until submission is established.
claude=assets/"claude_provider_c002.js"
if claude.exists():
    c=claude.read_text()
    # Generic helper works with textarea/contenteditable composers.
    if "function nexusClaudeSubmissionEstablished" not in c and "function composerText(" in c:
        marker="  function findSendButton()"
        if marker in c:
            helper="""  async function nexusClaudeSubmissionEstablished(composer,envelope,timeout=15000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const txt=composerText(composer).trim();
      const promptStillPresent=(envelope.context_pack_id&&txt.includes(envelope.context_pack_id))||txt.includes('Generate the completed Result Pack now.');
      if(!promptStillPresent && txt.length<40) return true;
      const body=String(document.body?.innerText||'');
      if(envelope.context_pack_id && body.includes(envelope.context_pack_id) && !promptStillPresent) return true;
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_ESTABLISHED');
  }

"""
            c=c.replace(marker,helper+marker,1)
    # Insert verification after a send click if a recognizable progress marker exists.
    patterns=[
      ("send.click();\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT');",
       "send.click();\n      await nexusClaudeSubmissionEstablished(composer,envelope);\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED');"),
      ("send.focus(); send.click();\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT');",
       "send.focus(); send.click();\n      await nexusClaudeSubmissionEstablished(composer,envelope);\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED');")
    ]
    for old,new in patterns:
        if old in c:
            c=c.replace(old,new,1)
            break
    claude.write_text(c)

m=main_path.read_text()

# Freshness/web intent is a REQUIRED research job, not generic OPTIONAL analysis.
old="""        val jobType = nexus.android.c002.core.JobType.OPEN_ANALYSIS
        val resolvedResearchPolicy = nexus.android.c002.core.resolveResearchPolicy(jobType)
"""
if old in m:
    new="""        val normalizedResearchIntent = userQuestion.lowercase()
        val explicitWebResearchRequested =
            listOf("recherche web", "recherche internet", "recherche en ligne", "web search", "search the web", "internet research")
                .any { normalizedResearchIntent.contains(it) }
        val freshnessRequested =
            Regex("\\b(aujourd['’]?hui|hier|derniers?\\s+(?:[0-9]+\\s+)?(?:jours?|heures?|semaines?)|derni[eè]res?\\s+(?:[0-9]+\\s+)?(?:jours?|heures?|semaines?)|r[eé]cent(?:e|es|s)?|latest|today|yesterday|last\\s+[0-9]+\\s+(?:days?|hours?|weeks?))\\b")
                .containsMatchIn(normalizedResearchIntent)
        val jobType = if (explicitWebResearchRequested || freshnessRequested)
            nexus.android.c002.core.JobType.POPINT_RESEARCH
        else
            nexus.android.c002.core.JobType.OPEN_ANALYSIS
        val resolvedResearchPolicy = nexus.android.c002.core.resolveResearchPolicy(jobType)
"""
    m=m.replace(old,new,1)

# Placeholder variants are never valid user answers.
old="""        val answer = resultPack.optString("answer").trim()
        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"
        if (answer == ANSWER_PLACEHOLDER) return "ANDROID_RESULT_ANSWER_PLACEHOLDER"
"""
if old in m:
    new="""        val answer = resultPack.optString("answer").trim()
        if (answer.isBlank()) return "ANDROID_RESULT_ANSWER_EMPTY"
        val normalizedAnswerToken = answer.replace(Regex("[^A-Za-z0-9]"), "").uppercase()
        if (answer == ANSWER_PLACEHOLDER || normalizedAnswerToken == "NEXUSMODELANSWER")
            return "ANDROID_RESULT_ANSWER_PLACEHOLDER"
"""
    m=m.replace(old,new,1)

# Expected pack is a template: research truth is supplied by provider and validated natively.
m=m.replace('                .put("external_research", false)\n',
            '                .put("external_research", JSONObject.NULL)\n',1)

# Manual confirmation means confirmed, not proven transport success.
m=m.replace('        productState.text = "$provider · connecté (confirmé par l’utilisateur)"',
            '        productState.text = "$provider · session confirmée · test d’exécution requis"',1)
m=m.replace('            productState.text = "${selectedProvider ?: "LLM"} · connecté · prêt"',
            '            productState.text = "${selectedProvider ?: "LLM"} · session détectée · prêt à tester"',1)

main_path.write_text(m)

# Bounded, selectable, scrollable result answer.
x=layout_path.read_text()
if 'android:id="@+id/resultAnswerScroll"' not in x:
    pattern=re.compile(r'''            <TextView\n                android:id="@\+id/resultSummary"\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="20dp"\n                android:padding="18dp"\n                android:background="#FFFFFF"\n                android:text="[^"]*"\n                android:textColor="#202123"\n                android:textSize="16sp"\n                android:lineSpacingExtra="4dp" />''')
    mm=pattern.search(x)
    if mm:
        block='''            <ScrollView
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
        x=x[:mm.start()]+block+x[mm.end():]
layout_path.write_text(x)

# Candidate identity.
b=gradle.read_text()
assert "versionCode = 76" in b
assert 'versionName = "0.0.76-v007-golden-recovery004-golden-diff-fix"' in b
b=b.replace("versionCode = 76","versionCode = 79",1)
b=b.replace('versionName = "0.0.76-v007-golden-recovery004-golden-diff-fix"',
            'versionName = "0.0.79-v007-golden-recovery007-provider-device-repair"',1)
gradle.write_text(b)

lock.write_text(lock.read_text()+
    "GOLDEN_RECOVERY007_BASE=RECOVERY004_CURRENT\n"
    "GOLDEN_RECOVERY007_DEVICE_OBSERVATIONS=GEMINI_GROK_ROUNDTRIP_PASS_CHATGPT_CAPTURE_FAIL_CLAUDE_SUBMIT_UNPROVEN_DEEPSEEK_PRE_DISPATCH_FAIL\n"
    "GOLDEN_RECOVERY007_PROMPT=SUBSTANTIVE_ANSWER_CONTRACT_RESTORED\n"
    "GOLDEN_RECOVERY007_FRESHNESS=RECENT_TIME_INTENT_TO_POPINT_REQUIRED\n"
    "GOLDEN_RECOVERY007_PROVIDER_BADGES=HIDDEN_NORMAL_UX_REPORT_RETAINS_DIAGNOSTICS\n"
    "GOLDEN_RECOVERY007_STATUS=MANUAL_CONFIRMATION_NOT_EQUAL_TRANSPORT_PASS\n"
    "GOLDEN_RECOVERY007_CHATGPT=CORRELATED_CAPTURE_FALLBACK\n"
    "GOLDEN_RECOVERY007_CLAUDE=SUBMISSION_CONFIRMATION_REQUIRED_WHEN_ADAPTER_ANCHOR_PRESENT\n"
    "GOLDEN_RECOVERY007_GEMINI=MANUAL_CONFIRM_WITH_VISIBLE_COMPOSER\n"
    "GOLDEN_RECOVERY007_RESULT_UI=SCROLLABLE_SELECTABLE\n"
    "GOLDEN_RECOVERY007_DEVICE_PASS=NOT_YET_ACQUIRED\n")

# Fail-closed static assertions.
out=main_path.read_text()
assert "POPINT_RESEARCH" in out and "freshnessRequested" in out
assert 'normalizedAnswerToken == "NEXUSMODELANSWER"' in out
assert "session confirmée · test d’exécution requis" in out
assert "versionCode = 79" in gradle.read_text()
for p in provider_files:
    js=p.read_text()
    assert "__NEXUS_MODEL_ANSWER__" not in js or "never return __NEXUS_MODEL_ANSWER__" in js
    if "badge.style.cssText" in js:
        assert "display:none" in js
if gem.exists():
    assert "Gemini UI session — exact backend model not exposed by bridge" in gem.read_text()
