from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / "app/src/main/assets/nexus"

gem = assets / "gemini_provider_c002.js"
zai = assets / "zai_provider_c002.js"
gradle = root / "app/build.gradle.kts"
lock = root / "RECONCILIATION_LOCK.txt"

# ---------------------------------------------------------------------------
# Gemini DEVICE repair: preserve certified send path; broaden only the
# submission-confirmation evidence so current Gemini DOM changes do not cause
# a false negative after an actual send.
# ---------------------------------------------------------------------------
g = gem.read_text()
assert "function modelResponseSnapshot()" in g
assert "GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED" in g

anchor = "  function generating(){\n"
helpers = """  function submittedUserPromptObserved(envelope){
    const selectors=[
      'user-query',
      '[data-test-id*="user-query" i]',
      '[data-testid*="user-message" i]',
      '[data-role="user" i]',
      '[data-message-author-role="user"]',
      '.query-text'
    ];
    const seen=new Set();
    for(const selector of selectors){
      for(const el of document.querySelectorAll(selector)){
        if(!visible(el)||seen.has(el)) continue;
        seen.add(el);
        const txt=String(el.innerText||el.textContent||'').trim();
        if(!txt) continue;
        if(envelope.context_pack_id && txt.includes(envelope.context_pack_id)) return true;
        if(envelope.question && txt.includes(String(envelope.question).slice(0,120))) return true;
        if(txt.includes('Generate the completed Result Pack now.')) return true;
      }
    }
    return false;
  }

"""
assert anchor in g
g = g.replace(anchor, helpers + anchor, 1)

pat = re.compile(r"  async function waitForSubmissionEstablished\(envelope,beforeSnapshot,timeout=12000\)\{.*?\n  \}\n\n  async function waitForModelResult", re.S)
m = pat.search(g)
assert m, "Gemini submission wait anchor missing"
replacement = """  async function waitForSubmissionEstablished(envelope,beforeSnapshot,timeout=20000){
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
      const userPromptObserved=submittedUserPromptObserved(envelope);
      if(promptGone||responseStarted||userPromptObserved){
        return {prompt_gone:promptGone,response_started:responseStarted,user_prompt_observed:userPromptObserved};
      }
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED');
  }

  async function waitForModelResult"""
g = g[:m.start()] + replacement + g[m.end():]

# ---------------------------------------------------------------------------
# Z.ai DEVICE repair: preserve certified send/submission logic; replace only
# final response capture with DOM-reuse-safe snapshot/candidate scanning.
# ---------------------------------------------------------------------------
z = zai.read_text()
assert "ZAI_UI_PROMPT_SENT_CONFIRMED" in z
assert "ZAI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON" in z

z = z.replace("  function parseCompleteResultCandidate(text){", "  function parseCompleteResultCandidate(text,envelope){", 1)
required_anchor = "const required=['result_pack_version','pack_id','comparison_id','model','answer','audit']; if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;"
assert required_anchor in z
z = z.replace(required_anchor, required_anchor + " if(envelope){ if(envelope.context_pack_id&&parsed.pack_id!==envelope.context_pack_id) continue; if(envelope.comparison_id&&parsed.comparison_id!==envelope.comparison_id) continue; }", 1)

anchor = "  function generating(){"
helpers = """  function responseNodeText(el){
    return String(el?.innerText||el?.textContent||'').trim();
  }
  function responseCandidateNodes(){
    const composer=findComposer();
    const selectors=[
      '.chat-assistant',
      '[data-testid*="assistant-message" i]',
      '[data-testid*="assistant" i]',
      '[data-role="assistant" i]',
      '[data-message-author-role="assistant"]',
      '.model-response-text',
      '.response-content',
      '.markdown',
      '[class*="markdown" i]',
      '.prose',
      '[class*="prose" i]',
      'pre',
      'code',
      'article',
      '[data-message-id]'
    ];
    const seen=new Set(), out=[];
    for(const selector of selectors){
      for(const el of document.querySelectorAll(selector)){
        if(!visible(el)||seen.has(el)) continue;
        if(composer && (el===composer || el.contains(composer) || composer.contains(el))) continue;
        const txt=responseNodeText(el);
        if(!txt) continue;
        seen.add(el); out.push(el);
      }
    }
    for(const el of responseNodes()){
      if(!seen.has(el)){ seen.add(el); out.push(el); }
    }
    return out;
  }
  function responseSnapshot(){
    return new Set(responseCandidateNodes().map(responseNodeText).filter(Boolean));
  }
"""
assert anchor in z
z = z.replace(anchor, helpers + "  function generating(){", 1)

pat = re.compile(r"  async function waitForModelResult\(bridgeRunId,beforeCount,timeout=160000\)\{.*?\n  \}\n  async function executeJob", re.S)
m = pat.search(z)
assert m, "Z.ai result wait anchor missing"
replacement = """  async function waitForModelResult(bridgeRunId,beforeSnapshot,envelope,timeout=180000){
    const deadline=Date.now()+timeout;
    let validText='',validSince=0,validParsed=null,lastCount=beforeSnapshot.size,lastChangedCount=0;
    while(Date.now()<deadline){
      const nodes=responseCandidateNodes();
      lastCount=nodes.length;
      const changed=nodes.filter(el=>{
        const txt=responseNodeText(el);
        return txt && !beforeSnapshot.has(txt);
      });
      lastChangedCount=changed.length;
      for(let i=changed.length-1;i>=0;i--){
        const txt=responseNodeText(changed[i]);
        const candidate=parseCompleteResultCandidate(txt,envelope);
        if(!candidate) continue;
        if(candidate.normalized_text===validText){
          if(!validSince) validSince=Date.now();
        }else{
          validText=candidate.normalized_text;
          validParsed=candidate.parsed;
          validSince=Date.now();
          await progress(bridgeRunId,'ZAI_JSON_COMPLETE_DETECTED');
        }
        if(Date.now()-validSince>=3000){
          return {text:validText,parsed:validParsed,node_count:nodes.length,changed_node_count:changed.length,json_stable_ms:Date.now()-validSince};
        }
        break;
      }
      await new Promise(r=>setTimeout(r,350));
    }
    throw new Error('ZAI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__candidate_nodes='+String(lastCount)+'__changed_nodes='+String(lastChangedCount));
  }
  async function executeJob"""
z = z[:m.start()] + replacement + z[m.end():]

old = "      const beforeCount=responseNodes().length; const prompt=buildPrompt(envelope); setComposerText(composer,prompt); const send=await waitForSendReady(composer);"
assert old in z
z = z.replace(old, "      const beforeCount=responseNodes().length; const beforeSnapshot=responseSnapshot(); const prompt=buildPrompt(envelope); setComposerText(composer,prompt); const send=await waitForSendReady(composer);", 1)
z = z.replace("const result=await waitForModelResult(bridgeRunId,beforeCount);", "const result=await waitForModelResult(bridgeRunId,beforeSnapshot,envelope);", 1)
meta = "response_count:result.node_count,"
assert meta in z
z = z.replace(meta, meta + "changed_response_count:result.changed_node_count||null,", 1)

gem.write_text(g)
zai.write_text(z)

# Candidate version only; no promotion/canonicalization implied.
x = gradle.read_text()
assert "versionCode = 73" in x
assert 'versionName = "0.0.73-v007-golden-recovery001"' in x
x = x.replace("versionCode = 73", "versionCode = 74", 1)
x = x.replace('versionName = "0.0.73-v007-golden-recovery001"', 'versionName = "0.0.74-v007-golden-recovery002-device-fixes"', 1)
gradle.write_text(x)

lock.write_text(lock.read_text() +
    "GOLDEN_RECOVERY002_GEMINI_DELTA=SUBMISSION_CONFIRMATION_SIGNALS_ONLY\n"
    "GOLDEN_RECOVERY002_ZAI_DELTA=RESULT_CAPTURE_SNAPSHOT_CANDIDATES_ONLY\n"
    "GOLDEN_RECOVERY002_GEMINI_SEND_PATH=PRESERVED\n"
    "GOLDEN_RECOVERY002_ZAI_SEND_PATH=PRESERVED\n"
    "GOLDEN_RECOVERY002_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Fail closed on scope drift.
gg = gem.read_text()
zz = zai.read_text()
assert "submittedUserPromptObserved(envelope)" in gg
assert "timeout=20000" in gg
assert "send.focus(); send.click();" in gg
assert "GEMINI_PROMPT_SUBMISSION_NOT_ESTABLISHED" in gg
assert "function responseSnapshot()" in zz
assert "responseCandidateNodes()" in zz
assert "waitForSubmissionEstablished(envelope,beforeCount)" in zz
assert "send.focus(); send.click();" in zz
assert "changed_response_count" in zz
assert "parseCompleteResultCandidate(txt,envelope)" in zz
