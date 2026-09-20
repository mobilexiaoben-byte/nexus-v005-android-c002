from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / "app/src/main/assets/nexus"

# ---------------------------------------------------------------------------
# Golden recovery delta.
# Base is the already-built Runtime019 WEB+MONITOR line, but generated from the
# frozen C003 baseline. Only response-capture logic is changed here.
# ChatGPT reference: GP-V005-CHATGPT-ANDROID-UIRETRY1 / commit cb82ece...
# Gemini reference: GP-V004-GEMINI-ANDROID-001 / commit 48494565...
# ---------------------------------------------------------------------------

chat = assets / "chatgpt_provider_c002.js"
s = chat.read_text()

# Preserve Golden UI retry/error behavior, but stop assuming a new assistant DOM
# node must be created. Modern ChatGPT can reuse/update an existing turn node.
marker = "  function parseCompleteResultCandidate(text){\n"
assert marker in s, "ChatGPT parse marker missing"
helpers = """  function assistantNodeText(el){
    return String(el?.innerText||el?.textContent||'').trim();
  }

  function assistantSnapshot(){
    return new Set(assistantNodes().map(assistantNodeText).filter(Boolean));
  }

"""
s = s.replace(marker, helpers + "  function parseCompleteResultCandidate(text,envelope){\n", 1)

old_required = """        const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
        if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
        return {parsed,normalized_text:candidate};
"""
new_required = """        const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
        if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
        if(envelope){
          if(envelope.context_pack_id && parsed.pack_id!==envelope.context_pack_id) continue;
          if(envelope.comparison_id && parsed.comparison_id!==envelope.comparison_id) continue;
        }
        return {parsed,normalized_text:candidate};
"""
assert old_required in s, "ChatGPT required fields anchor missing"
s = s.replace(old_required, new_required, 1)

pat = re.compile(r"  async function waitForAssistantResult\(beforeCount, timeout=80000, errorGraceUntil=0\)\{.*?\n  \}\n\n  async function executeJob", re.S)
m = pat.search(s)
assert m, "ChatGPT Golden UIRETRY1 wait function anchor missing"
new_wait = """  async function waitForAssistantResult(beforeSnapshot, envelope, timeout=80000, errorGraceUntil=0){
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
          return {
            text:validText,
            parsed:validParsed,
            node_count:nodes.length,
            changed_node_count:changed.length,
            json_stable_ms:Date.now()-validSince
          };
        }
        break;
      }
      await new Promise(r=>setTimeout(r,350));
    }
    throw new Error(
      'CHATGPT_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__assistant_nodes='+
      String(lastNodeCount)+'__changed_nodes='+String(lastChangedCount)
    );
  }

  async function executeJob"""
s = s[:m.start()] + new_wait + s[m.end():]

assert "const beforeCount=assistantNodes().length;" in s, "ChatGPT beforeCount anchor missing"
s = s.replace("const beforeCount=assistantNodes().length;", "const beforeSnapshot=assistantSnapshot();", 1)
s = s.replace("waitForAssistantResult(beforeCount,80000)", "waitForAssistantResult(beforeSnapshot,envelope,80000)", 1)
s = s.replace("waitForAssistantResult(beforeCount,80000,graceUntil)", "waitForAssistantResult(beforeSnapshot,envelope,80000,graceUntil)", 1)
meta_anchor = "          assistant_node_count:result.node_count,\n"
assert meta_anchor in s, "ChatGPT provider_meta anchor missing"
s = s.replace(meta_anchor, meta_anchor + "          changed_assistant_count:result.changed_node_count||null,\n", 1)
assert "beforeCount=assistantNodes().length" not in s
assert "assistantSnapshot()" in s
assert "parseCompleteResultCandidate(txt,envelope)" in s
chat.write_text(s)

gem = assets / "gemini_provider_c002.js"
g = gem.read_text()

# Same principle for Gemini: preserve the proven selectors/submission contract,
# but detect response text mutation rather than requiring nodes.length growth.
marker = "  function generating(){\n"
assert marker in g, "Gemini generating marker missing"
helpers = """  function modelNodeText(el){
    return String(el?.innerText||el?.textContent||'').trim();
  }

  function modelResponseSnapshot(){
    return new Set(modelResponseNodes().map(modelNodeText).filter(Boolean));
  }

"""
g = g.replace(marker, helpers + marker, 1)

g = g.replace("  function parseCompleteResultCandidate(text){", "  function parseCompleteResultCandidate(text,envelope){", 1)
assert old_required in g, "Gemini required fields anchor missing"
g = g.replace(old_required, new_required, 1)

pat = re.compile(r"  async function waitForSubmissionEstablished\(envelope,beforeCount,timeout=12000\)\{.*?\n  \}\n\n  async function waitForModelResult\(bridgeRunId,beforeCount,timeout=160000\)\{.*?\n  \}\n", re.S)
m = pat.search(g)
assert m, "Gemini wait functions anchor missing"
new_gwait = """  async function waitForSubmissionEstablished(envelope,beforeSnapshot,timeout=12000){
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
          return {
            text:validText,
            parsed:validParsed,
            node_count:nodes.length,
            changed_node_count:changed.length,
            json_stable_ms:Date.now()-validSince
          };
        }
        break;
      }
      await new Promise(r=>setTimeout(r,350));
    }
    throw new Error(
      'GEMINI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__model_nodes='+
      String(lastCount)+'__changed_nodes='+String(lastChangedCount)
    );
  }
"""
g = g[:m.start()] + new_gwait + g[m.end():]
assert "const beforeCount=modelResponseNodes().length;" in g, "Gemini beforeCount anchor missing"
g = g.replace("const beforeCount=modelResponseNodes().length;", "const beforeSnapshot=modelResponseSnapshot();", 1)
g = g.replace("waitForSubmissionEstablished(envelope,beforeCount)", "waitForSubmissionEstablished(envelope,beforeSnapshot)", 1)
g = g.replace("waitForModelResult(bridgeRunId,beforeCount)", "waitForModelResult(bridgeRunId,beforeSnapshot,envelope)", 1)
meta_anchor = "          model_response_count:result.node_count,\n"
assert meta_anchor in g, "Gemini provider_meta anchor missing"
g = g.replace(meta_anchor, meta_anchor + "          changed_response_count:result.changed_node_count||null,\n", 1)
assert "beforeCount=modelResponseNodes().length" not in g
assert "modelResponseSnapshot()" in g
assert "parseCompleteResultCandidate(txt,envelope)" in g
gem.write_text(g)

# Candidate identity: successor of Runtime019 WEB+MONITOR, not a new policy/UX design.
gradle = root / "app/build.gradle.kts"
x = gradle.read_text()
assert "versionCode = 72" in x
assert 'versionName = "0.0.72-v007-m024-u013-provider-runtime019-web-monitor-fix"' in x
x=x.replace("versionCode = 72","versionCode = 73",1)
x=x.replace(
    'versionName = "0.0.72-v007-m024-u013-provider-runtime019-web-monitor-fix"',
    'versionName = "0.0.73-v007-golden-recovery001"',
    1
)
gradle.write_text(x)

lock=root/"RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text()+
    "GOLDEN_RECOVERY001_BASELINE=C003_SHA_69f88ce310515d94c7225a080d615c64c7bc3dac786cc2a9d590901599fa6670\n"
    "GOLDEN_RECOVERY001_CHATGPT=GP-V005-CHATGPT-ANDROID-UIRETRY1_BEHAVIOR_PRESERVED\n"
    "GOLDEN_RECOVERY001_GEMINI=GP-V004-GEMINI-ANDROID-001_BEHAVIOR_PRESERVED\n"
    "GOLDEN_RECOVERY001_CAPTURE_DELTA=TEXT_SNAPSHOT_DIFF_NOT_NODECOUNT\n"
    "GOLDEN_RECOVERY001_M024_WEB=RUNTIME019_WEB_MONITOR_FIX_PRESERVED\n"
    "GOLDEN_RECOVERY001_REPORT=READABLE_TERMINAL_STOP_PRESERVED\n"
    "GOLDEN_RECOVERY001_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)
