from pathlib import Path
import re, sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

exec((repo / "reconcile018" / "provider_runtime_018.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile018" / "provider_runtime_018.py"),
    "sys": sys,
})

gem_path = root / "app/src/main/assets/nexus/gemini_provider_c002.js"
s = gem_path.read_text()

old = """  function modelResponseNodes(){
    const primary=[...document.querySelectorAll('model-response')].filter(visible);
    if(primary.length) return primary;
    const selectors=['[data-test-id*="model-response" i]','.model-response-text','message-content','.response-content'];
    const seen=new Set(),out=[];
    for(const s of selectors){
      for(const el of document.querySelectorAll(s)){
        if(!visible(el)||seen.has(el)) continue;
        seen.add(el); out.push(el);
      }
    }
    return out;
  }

  function generating(){"""
new = """  function modelResponseNodes(){
    const selectors=[
      'model-response',
      '[data-message-author-role="model"]',
      '[data-test-id*="model-response" i]',
      '[data-test-id*="response" i]',
      'message-content',
      '.model-response-text',
      '.response-content',
      '[class*="model-response" i]',
      '[class*="response-content" i]'
    ];
    const seen=new Set(),out=[];
    for(const selector of selectors){
      for(const el of document.querySelectorAll(selector)){
        if(!visible(el)||seen.has(el)) continue;
        if(el.closest && el.closest('rich-textarea,[contenteditable="true"][role="textbox"]')) continue;
        seen.add(el); out.push(el);
      }
    }
    return out;
  }

  function nodeText(el){
    return String(el?.innerText||el?.textContent||'').trim();
  }

  function responseSnapshot(){
    return new Set(modelResponseNodes().map(nodeText).filter(Boolean));
  }

  function responseChanged(nodes,beforeSnapshot){
    return nodes.some(el=>{
      const txt=nodeText(el);
      return txt && !beforeSnapshot.has(txt);
    });
  }

  function generating(){"""
assert s.count(old)==1, "modelResponseNodes exact anchor mismatch"
s=s.replace(old,new,1)

s = s.replace(
    "  function parseCompleteResultCandidate(text){",
    "  function parseCompleteResultCandidate(text,envelope){",
    1
)
old = """        const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
        if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
        return {parsed,normalized_text:candidate};
"""
new = """        const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
        if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
        if(envelope){
          if(envelope.context_pack_id && parsed.pack_id!==envelope.context_pack_id) continue;
          if(envelope.comparison_id && parsed.comparison_id!==envelope.comparison_id) continue;
        }
        return {parsed,normalized_text:candidate};
"""
assert s.count(old)==1, "parse validation anchor mismatch"
s=s.replace(old,new,1)

old = """  async function waitForSubmissionEstablished(envelope,beforeCount,timeout=12000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const composer=findComposer();
      const text=composerText(composer).trim();
      const promptGone=!text.includes(envelope.context_pack_id)&&!text.includes('Generate the completed Result Pack now.');
      const responseStarted=modelResponseNodes().length>beforeCount||generating();
      if(promptGone||responseStarted) return {prompt_gone:promptGone,response_started:responseStarted};
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED');
  }

  async function waitForModelResult(bridgeRunId,beforeCount,timeout=160000){
    const deadline=Date.now()+timeout;
    let validText='',validSince=0,validParsed=null,lastCount=beforeCount;
    while(Date.now()<deadline){
      const nodes=modelResponseNodes();
      lastCount=nodes.length;
      if(nodes.length>beforeCount){
        const txt=String(nodes[nodes.length-1].innerText||nodes[nodes.length-1].textContent||'').trim();
        const candidate=parseCompleteResultCandidate(txt);
        if(candidate){
          if(candidate.normalized_text===validText){ if(!validSince) validSince=Date.now(); }
          else { validText=candidate.normalized_text; validParsed=candidate.parsed; validSince=Date.now(); await progress(bridgeRunId,'GEMINI_JSON_COMPLETE_DETECTED'); }
          if(Date.now()-validSince>=5000){
            return {text:validText,parsed:validParsed,node_count:nodes.length,json_stable_ms:Date.now()-validSince};
          }
        }else{
          validText=''; validParsed=null; validSince=0;
        }
      }
      await new Promise(r=>setTimeout(r,400));
    }
    throw new Error('GEMINI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__model_nodes='+String(lastCount));
  }
"""
new = """  async function waitForSubmissionEstablished(envelope,beforeSnapshot,timeout=12000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const composer=findComposer();
      const text=composerText(composer).trim();
      const promptGone=!text.includes(envelope.context_pack_id)&&!text.includes('Generate the completed Result Pack now.');
      const nodes=modelResponseNodes();
      const responseStarted=responseChanged(nodes,beforeSnapshot)||generating();
      if(promptGone||responseStarted) return {prompt_gone:promptGone,response_started:responseStarted};
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED');
  }

  async function waitForModelResult(bridgeRunId,beforeSnapshot,envelope,timeout=175000){
    const deadline=Date.now()+timeout;
    let validText='',validSince=0,validParsed=null,lastCount=beforeSnapshot.size,lastChangedCount=0;
    while(Date.now()<deadline){
      const nodes=modelResponseNodes();
      lastCount=nodes.length;
      const changed=nodes.filter(el=>{
        const txt=nodeText(el);
        return txt && !beforeSnapshot.has(txt);
      });
      lastChangedCount=changed.length;
      for(let i=changed.length-1;i>=0;i--){
        const txt=nodeText(changed[i]);
        const candidate=parseCompleteResultCandidate(txt,envelope);
        if(!candidate) continue;
        if(candidate.normalized_text===validText){ if(!validSince) validSince=Date.now(); }
        else {
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
assert s.count(old)==1, "Gemini wait functions anchor mismatch"
s=s.replace(old,new,1)

old = """      const beforeCount=modelResponseNodes().length;
      const prompt=buildPrompt(envelope);
"""
new = """      const beforeSnapshot=responseSnapshot();
      const prompt=buildPrompt(envelope);
"""
assert s.count(old)==1, "beforeCount anchor mismatch"
s=s.replace(old,new,1)
s=s.replace(
    "      const submission=await waitForSubmissionEstablished(envelope,beforeCount);",
    "      const submission=await waitForSubmissionEstablished(envelope,beforeSnapshot);",
    1
)
s=s.replace(
    "      const result=await waitForModelResult(bridgeRunId,beforeCount);",
    "      const result=await waitForModelResult(bridgeRunId,beforeSnapshot,envelope);",
    1
)
old = """          model_response_count:result.node_count,
          json_stable_ms:result.json_stable_ms||null,
"""
new = """          model_response_count:result.node_count,
          changed_response_count:result.changed_node_count||null,
          json_stable_ms:result.json_stable_ms||null,
"""
assert s.count(old)==1, "provider_meta anchor mismatch"
s=s.replace(old,new,1)

# Ensure legacy count-only capture is gone.
assert "nodes.length>beforeCount" not in s
assert "beforeCount=modelResponseNodes().length" not in s
assert "responseSnapshot()" in s
assert "responseChanged(nodes,beforeSnapshot)" in s
assert "parseCompleteResultCandidate(txt,envelope)" in s
assert "changed_response_count" in s
gem_path.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 71" in g
assert 'versionName = "0.0.71-v007-m024-u013-provider-runtime018-provider-origin-fix"' in g
g=g.replace("versionCode = 71","versionCode = 72",1)
g=g.replace(
    'versionName = "0.0.71-v007-m024-u013-provider-runtime018-provider-origin-fix"',
    'versionName = "0.0.72-v007-m024-u013-provider-runtime019-gemini-capture-fix"',
    1
)
gradle.write_text(g)

lock=root/"RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text()+
    "PROVIDER_RUNTIME019_BASE=RUNTIME018_PROVIDER_ORIGIN_FIX\n"
    "PROVIDER_RUNTIME019_GEMINI_CAPTURE=DOM_REUSE_SAFE_SNAPSHOT_DIFF\n"
    "PROVIDER_RUNTIME019_GEMINI_SELECTORS=BROAD_MODEL_RESPONSE_SET\n"
    "PROVIDER_RUNTIME019_RESULT_CORRELATION=PACK_ID_AND_COMPARISON_ID\n"
    "PROVIDER_RUNTIME019_GEMINI_TIMEOUT=175000_PROVIDER_LT_190000_NATIVE\n"
    "PROVIDER_RUNTIME018_ORIGIN_GATE=PRESERVED\n"
    "M024_RUNTIME016_POLICY_ROUTER=PRESERVED\n"
    "ZAI_RUNTIME018_DEVICE_ANALYSIS=USER_REPORTED_PASS_20260920\n"
    "V009_ARCH005=FROZEN_UNMODIFIED\n"
    "GEMINI_RUNTIME019_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Final generated-source assertions.
assert 'versionCode = 72' in gradle.read_text()
assert '0.0.72-v007-m024-u013-provider-runtime019-gemini-capture-fix' in gradle.read_text()
