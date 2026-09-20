from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / "app/src/main/assets/nexus"
main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"

policy_expr = """(researchPolicy==='FORBIDDEN'
        ?'- Research policy FORBIDDEN: do not browse the web or perform external research.'
        :researchPolicy==='REQUIRED'
          ?'- Research policy REQUIRED: perform external research when available and permitted; preserve source traceability.'
          :researchPolicy==='REQUIRED_IF_STALE'
            ?'- Research policy REQUIRED_IF_STALE: perform external research when freshness or source gaps require it and it is permitted.'
            :'- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy.')"""

def adapt_policy_and_ready(s):
    # M024 resolved research_policy is the authority; keep Golden transport logic.
    s=s.replace("ALLOWED","OPTIONAL")
    s=s.replace("      if(envelope.external_research!==false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');\n","")
    s=s.replace("      if (envelope.external_research !== false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');\n","")
    marker="function buildPrompt(envelope){"
    assert marker in s
    pos=s.index(marker)
    if "const researchPolicy=" not in s[pos:pos+500]:
        s=s.replace(marker,marker+"\n    const researchPolicy=String(envelope.research_policy||'FORBIDDEN');",1)
    for ban in [
        "'- Do NOT browse the web and do NOT perform external research.',",
        '"- Do NOT browse the web and do NOT perform external research.",',
    ]:
        if ban in s:
            s=s.replace(ban,policy_expr+",",1)
    if "type:'BRIDGE_READY'" not in s:
        marker="  console.info("
        assert marker in s
        s=s.replace(marker,
            "  [0,100,300,1000].forEach((delay)=>setTimeout(()=>{nativeSend({channel:CHANNEL,type:'BRIDGE_READY'}).catch(()=>{});},delay));\n"+marker,
            1)
    return s

def add_result_correlation(s):
    pat=re.compile(r"(\s*const required=\['result_pack_version','pack_id','comparison_id','model','answer','audit'\];\n\s*if\(!required\.every\(k=>Object\.prototype\.hasOwnProperty\.call\(parsed,k\)\)\) continue;)")
    m=pat.search(s)
    assert m, "Result Pack required-fields anchor missing"
    inject=m.group(1)+"""
        if(envelope){
          if(envelope.context_pack_id && parsed.pack_id!==envelope.context_pack_id) continue;
          if(envelope.comparison_id && parsed.comparison_id!==envelope.comparison_id) continue;
        }"""
    return s[:m.start()]+inject+s[m.end():]

# ---------------------------------------------------------------------------
# ChatGPT: exact UIRETRY1 DEVICE-PASS adapter was copied into the candidate by
# the workflow. Preserve its retry/error logic; only make response observation
# DOM-reuse-safe and bind output to the current envelope.
# ---------------------------------------------------------------------------
chat=assets/"chatgpt_provider_c002.js"
s=adapt_policy_and_ready(chat.read_text())
assert "function findRetryButton()" in s
assert "CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE" in s
s=s.replace("  function parseCompleteResultCandidate(text){","  function parseCompleteResultCandidate(text,envelope){",1)
s=add_result_correlation(s)
marker="  function parseCompleteResultCandidate(text,envelope){\n"
helpers="""  function assistantNodeText(el){
    return String(el?.innerText||el?.textContent||'').trim();
  }

  function assistantSnapshot(){
    return new Set(assistantNodes().map(assistantNodeText).filter(Boolean));
  }

"""
assert marker in s
s=s.replace(marker,helpers+marker,1)
pat=re.compile(r"  async function waitForAssistantResult\(beforeCount, timeout=80000, errorGraceUntil=0\)\{.*?\n  \}\n\n  async function executeJob",re.S)
m=pat.search(s)
assert m,"ChatGPT UIRETRY1 wait anchor missing"
wait="""  async function waitForAssistantResult(beforeSnapshot, envelope, timeout=80000, errorGraceUntil=0){
    const deadline=Date.now()+timeout;
    let validText='',validSince=0,validParsed=null,lastNodeCount=beforeSnapshot.size,lastChangedCount=0;
    while(Date.now()<deadline){
      if(Date.now()>=errorGraceUntil){
        const uiError=detectUiResponseError();
        if(uiError){
          throw new Error(uiError.retry_available ? 'CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE' : 'CHATGPT_UI_RESPONSE_ERROR_NO_RETRY_CONTROL');
        }
      }
      const nodes=assistantNodes();
      lastNodeCount=nodes.length;
      const changed=nodes.filter(el=>{
        const txt=assistantNodeText(el);
        return txt && !beforeSnapshot.has(txt);
      });
      lastChangedCount=changed.length;
      for(let i=changed.length-1;i>=0;i--){
        const txt=assistantNodeText(changed[i]);
        const candidate=parseCompleteResultCandidate(txt,envelope);
        if(!candidate) continue;
        if(candidate.normalized_text===validText){
          if(!validSince) validSince=Date.now();
        }else{
          validText=candidate.normalized_text;
          validParsed=candidate.parsed;
          validSince=Date.now();
          show('JSON complet détecté — stabilité en cours');
        }
        if(Date.now()-validSince>=3000){
          return {text:validText,parsed:validParsed,node_count:nodes.length,changed_node_count:changed.length,json_stable_ms:Date.now()-validSince};
        }
        break;
      }
      await new Promise(r=>setTimeout(r,350));
    }
    throw new Error('CHATGPT_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__assistant_nodes='+String(lastNodeCount)+'__changed_nodes='+String(lastChangedCount));
  }

  async function executeJob"""
s=s[:m.start()]+wait+s[m.end():]
assert "const beforeCount=assistantNodes().length;" in s
s=s.replace("const beforeCount=assistantNodes().length;","const beforeSnapshot=assistantSnapshot();",1)
s=s.replace("waitForAssistantResult(beforeCount,80000)","waitForAssistantResult(beforeSnapshot,envelope,80000)",1)
s=s.replace("waitForAssistantResult(beforeCount,80000,graceUntil)","waitForAssistantResult(beforeSnapshot,envelope,80000,graceUntil)",1)
meta="          assistant_node_count:result.node_count,\n"
assert meta in s
s=s.replace(meta,meta+"          changed_assistant_count:result.changed_node_count||null,\n",1)
chat.write_text(s)

# ---------------------------------------------------------------------------
# Gemini: exact V004 DEVICE-PASS provider asset copied by workflow. Preserve its
# composer/send/submission contract; only make result capture DOM-reuse-safe,
# adapt M024 research policy and keep the Golden channel end-to-end.
# ---------------------------------------------------------------------------
gem=assets/"gemini_provider_c002.js"
g=adapt_policy_and_ready(gem.read_text())
assert "const CHANNEL='NEXUS_V004_GEMINI_001'" in g
g=g.replace("  function parseCompleteResultCandidate(text){","  function parseCompleteResultCandidate(text,envelope){",1)
g=add_result_correlation(g)
marker="  function generating(){\n"
helpers="""  function modelNodeText(el){
    return String(el?.innerText||el?.textContent||'').trim();
  }

  function modelResponseSnapshot(){
    return new Set(modelResponseNodes().map(modelNodeText).filter(Boolean));
  }

"""
assert marker in g
g=g.replace(marker,helpers+marker,1)
pat=re.compile(r"  async function waitForSubmissionEstablished\(envelope,beforeCount,timeout=12000\)\{.*?\n  \}\n\n  async function waitForModelResult\(bridgeRunId,beforeCount,timeout=160000\)\{.*?\n  \}\n",re.S)
m=pat.search(g)
assert m,"Gemini Golden wait anchors missing"
gw="""  async function waitForSubmissionEstablished(envelope,beforeSnapshot,timeout=12000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const composer=findComposer();
      const text=composerText(composer).trim();
      const promptGone=!text.includes(envelope.context_pack_id)&&!text.includes('Generate the completed Result Pack now.');
      const nodes=modelResponseNodes();
      const responseStarted=nodes.some(el=>{
        const txt=modelNodeText(el);
        return txt && !beforeSnapshot.has(txt);
      })||generating();
      if(promptGone||responseStarted) return {prompt_gone:promptGone,response_started:responseStarted};
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED');
  }

  async function waitForModelResult(bridgeRunId,beforeSnapshot,envelope,timeout=170000){
    const deadline=Date.now()+timeout;
    let validText='',validSince=0,validParsed=null,lastCount=beforeSnapshot.size,lastChangedCount=0;
    while(Date.now()<deadline){
      const nodes=modelResponseNodes();
      lastCount=nodes.length;
      const changed=nodes.filter(el=>{
        const txt=modelNodeText(el);
        return txt && !beforeSnapshot.has(txt);
      });
      lastChangedCount=changed.length;
      for(let i=changed.length-1;i>=0;i--){
        const txt=modelNodeText(changed[i]);
        const candidate=parseCompleteResultCandidate(txt,envelope);
        if(!candidate) continue;
        if(candidate.normalized_text===validText){
          if(!validSince) validSince=Date.now();
        }else{
          validText=candidate.normalized_text;
          validParsed=candidate.parsed;
          validSince=Date.now();
          await progress(bridgeRunId,'GEMINI_JSON_COMPLETE_DETECTED');
        }
        if(Date.now()-validSince>=3000){
          return {text:validText,parsed:validParsed,node_count:nodes.length,changed_node_count:changed.length,json_stable_ms:Date.now()-validSince};
        }
        break;
      }
      await new Promise(r=>setTimeout(r,350));
    }
    throw new Error('GEMINI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__model_nodes='+String(lastCount)+'__changed_nodes='+String(lastChangedCount));
  }
"""
g=g[:m.start()]+gw+g[m.end():]
assert "const beforeCount=modelResponseNodes().length;" in g
g=g.replace("const beforeCount=modelResponseNodes().length;","const beforeSnapshot=modelResponseSnapshot();",1)
g=g.replace("waitForSubmissionEstablished(envelope,beforeCount)","waitForSubmissionEstablished(envelope,beforeSnapshot)",1)
g=g.replace("waitForModelResult(bridgeRunId,beforeCount)","waitForModelResult(bridgeRunId,beforeSnapshot,envelope)",1)
meta="          model_response_count:result.node_count,\n"
assert meta in g
g=g.replace(meta,meta+"          changed_response_count:result.changed_node_count||null,\n",1)
gem.write_text(g)

# Current controller must speak the Golden Gemini channel used by the restored adapter.
m=main_path.read_text()
assert 'const val GEMINI_CHANNEL = "NEXUS_V007_GEMINI_DIAG_003"' in m
m=m.replace('const val GEMINI_CHANNEL = "NEXUS_V007_GEMINI_DIAG_003"','const val GEMINI_CHANNEL = "NEXUS_V004_GEMINI_001"',1)
main_path.write_text(m)

gradle=root/"app/build.gradle.kts"
x=gradle.read_text()
assert "versionCode = 72" in x
assert 'versionName = "0.0.72-v007-m024-u013-provider-runtime019-web-monitor-fix"' in x
x=x.replace("versionCode = 72","versionCode = 73",1)
x=x.replace('versionName = "0.0.72-v007-m024-u013-provider-runtime019-web-monitor-fix"','versionName = "0.0.73-v007-golden-recovery001"',1)
gradle.write_text(x)

lock=root/"RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text()+
    "GOLDEN_RECOVERY001_BASELINE=C003_SHA_69f88ce310515d94c7225a080d615c64c7bc3dac786cc2a9d590901599fa6670\n"
    "GOLDEN_RECOVERY001_CHATGPT_SOURCE=GP-V005-CHATGPT-ANDROID-UIRETRY1_HEAD_cb82ece5e9a29a21115b5127cee69fd5b9a06987\n"
    "GOLDEN_RECOVERY001_GEMINI_SOURCE=GP-V004-GEMINI-ANDROID-001_HEAD_48494565af818bf6859ba4fa90e2e8d0db0397fa\n"
    "GOLDEN_RECOVERY001_CAPTURE_DELTA=TEXT_SNAPSHOT_DIFF_NOT_NODECOUNT\n"
    "GOLDEN_RECOVERY001_M024_WEB=OPTIONAL_POLICY_PRESERVED\n"
    "GOLDEN_RECOVERY001_REPORT=READABLE_TERMINAL_STOP_PRESERVED\n"
    "GOLDEN_RECOVERY001_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Fail closed on accidental drift from intended repair.
for p in [chat,gem]:
    js=p.read_text()
    assert "Do NOT browse the web and do NOT perform external research" not in js
    assert "type:'BRIDGE_READY'" in js
    assert "research_policy" in js
assert "function findRetryButton()" in chat.read_text()
assert "NEXUS_V004_GEMINI_001" in gem.read_text()
assert 'const val GEMINI_CHANNEL = "NEXUS_V004_GEMINI_001"' in main_path.read_text()
