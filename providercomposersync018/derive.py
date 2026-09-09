from pathlib import Path
import subprocess
import sys

repo=Path(sys.argv[1]).resolve()
work=Path(sys.argv[2]).resolve()
subprocess.run(['python3', str(repo/'claudeturngeneration017'/'derive.py'), str(repo), str(work)], check=True)
root=work

p=root/'app/build.gradle.kts'; g=p.read_text()
for before,after in [
('applicationId = "nexus.android.c002.claudeturngeneration017"','applicationId = "nexus.android.c002.providercomposersync018"'),
('versionCode = 18','versionCode = 19'),
('versionName = "0.0.18-c002-claude-turngeneration017"','versionName = "0.0.19-c002-provider-composersync018"')]:
    assert g.count(before)==1, before; g=g.replace(before,after)
p.write_text(g)

p=root/'app/src/main/AndroidManifest.xml'; m=p.read_text(); old='android:label="NEXUS C002 CLAUDE TURN GENERATION DIAG 017"'; assert m.count(old)==1; p.write_text(m.replace(old,'android:label="NEXUS C002 PROVIDER COMPOSER SYNC 018"'))

main=root/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=main.read_text()
for before,after in [
('nexus_provider_profile_c002_claude_turngeneration017','nexus_provider_profile_c002_provider_composersync018'),
('V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017-BRIDGE-001','V005-C002-PROVIDER-COMPOSER-STATE-SYNC-018-BRIDGE-001'),
('V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017-001','V005-C002-PROVIDER-COMPOSER-STATE-SYNC-018-001'),
('V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017-COMP-001','V005-C002-PROVIDER-COMPOSER-STATE-SYNC-018-COMP-001'),
('V005_CLAUDE_TURN_GENERATION_DIAGNOSTIC_017_V1','V005_PROVIDER_COMPOSER_STATE_SYNC_018_V1'),
('NEXUS_CLAUDE_TURN_GENERATION_DIAGNOSTIC_017_OK','NEXUS_PROVIDER_COMPOSER_STATE_SYNC_018_OK'),
('this Android Claude turn-generation diagnostic proof','this Android provider composer-state synchronization proof'),
('.put("contract", "V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017")','.put("contract", "V005-C002-PROVIDER-COMPOSER-STATE-SYNC-018")')]:
    assert before in s, before; s=s.replace(before,after)

when_anchor='''            type == "PROVIDER_PROGRESS" -> handleProviderProgress(message)\n            type == "PROVIDER_RESULT" -> handleProviderResult(normalizedOrigin, message)\n'''
when_new='''            type == "PROVIDER_PROGRESS" -> handleProviderProgress(message)\n            type == "PROVIDER_UI_ACTUATE" -> handleProviderUiActuate(normalizedOrigin, message)\n            type == "PROVIDER_RESULT" -> handleProviderResult(normalizedOrigin, message)\n'''
assert s.count(when_anchor)==1; s=s.replace(when_anchor,when_new)

insert_anchor='''    private fun handleProviderAck(message: JSONObject) {\n'''
handler=r'''    private fun handleProviderUiActuate(origin: String, message: JSONObject) {
        if (!executionStarted || proofStopped || terminalReceived) return
        if (message.optString("bridge_run_id") != BRIDGE_RUN_ID) {
            block("ANDROID_UI_ACTUATE_CORRELATION_MISMATCH")
            return
        }
        val requestId = message.optString("request_id")
        if (!requestId.matches(Regex("[A-Za-z0-9._:-]{1,96}"))) {
            block("ANDROID_UI_ACTUATE_REQUEST_ID_INVALID")
            return
        }
        if (message.optString("action") != "SET_COMPOSER_TEXT") {
            block("ANDROID_UI_ACTUATE_ACTION_BLOCKED")
            return
        }
        val text = message.optString("text")
        val job = proofJob ?: run {
            block("ANDROID_UI_ACTUATE_JOB_STATE_MISSING")
            return
        }
        if (text.length !in 20..200_000 || !text.contains(job.contextPackId) || !text.contains(job.frozenFingerprint)) {
            block("ANDROID_UI_ACTUATE_PAYLOAD_MISMATCH")
            return
        }
        fun readSelectors(key: String): List<String>? {
            val arr = message.optJSONArray(key) ?: return null
            if (arr.length() !in 1..12) return null
            return (0 until arr.length()).map { arr.optString(it) }.takeIf { values ->
                values.all { value -> value.isNotBlank() && value.length <= 180 && value.none { ch -> ch.code < 32 || ch.code == 127 } }
            }
        }
        val composerSelectors = readSelectors("composer_selectors") ?: run {
            block("ANDROID_UI_ACTUATE_COMPOSER_SELECTORS_INVALID")
            return
        }
        val sendSelectors = readSelectors("send_selectors") ?: run {
            block("ANDROID_UI_ACTUATE_SEND_SELECTORS_INVALID")
            return
        }
        val channel = providerChannel ?: run {
            block("ANDROID_UI_ACTUATE_CHANNEL_UNBOUND")
            return
        }
        val script = buildProviderComposerActuationScript(text, composerSelectors, sendSelectors)
        recordDiagnostic("PROVIDER_UI_ACTUATE", origin, "request_id=$requestId;action=SET_COMPOSER_TEXT")
        val accepted = bridge?.executePageWorld(origin, script) { raw ->
            val result = decodePageWorldResult(raw)
            val outbound = JSONObject()
                .put("channel", channel)
                .put("type", "PROVIDER_UI_ACTUATE_RESULT")
                .put("bridge_run_id", BRIDGE_RUN_ID)
                .put("request_id", requestId)
                .put("result", result)
            if (bridge?.post(origin, outbound.toString()) != true && !proofStopped) {
                block("ANDROID_UI_ACTUATE_RESULT_POST_FAILED")
            }
        } == true
        if (!accepted) block("ANDROID_UI_ACTUATE_PAGE_WORLD_EXECUTION_REJECTED")
    }

    private fun decodePageWorldResult(raw: String): JSONObject {
        return runCatching {
            val decoded = JSONArray("[$raw]").optString(0)
            JSONObject(decoded)
        }.getOrElse {
            JSONObject().put("ok", false).put("error", "PAGE_WORLD_RESULT_MALFORMED")
        }
    }

    private fun buildProviderComposerActuationScript(
        text: String,
        composerSelectors: List<String>,
        sendSelectors: List<String>
    ): String {
        val jsText = JSONObject.quote(text)
        val jsComposerSelectors = JSONArray(composerSelectors).toString()
        val jsSendSelectors = JSONArray(sendSelectors).toString()
        return """
            (() => {
              const text=$jsText;
              const composerSelectors=$jsComposerSelectors;
              const sendSelectors=$jsSendSelectors;
              const visible=(el)=>{
                if(!el||!el.isConnected) return false;
                const cs=getComputedStyle(el);
                if(cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0) return false;
                const r=el.getBoundingClientRect(); return r.width>0&&r.height>0;
              };
              const composerText=(el)=>('value' in el&&typeof el.value==='string')?el.value:(el.innerText||el.textContent||'');
              let composer=null;
              for(const sel of composerSelectors){
                for(const el of document.querySelectorAll(sel)){ if(visible(el)){ composer=el; break; } }
                if(composer) break;
              }
              if(!composer) return JSON.stringify({ok:false,error:'COMPOSER_NOT_FOUND'});
              composer.focus();
              let method='UNKNOWN';
              try{
                if(composer.tagName==='TEXTAREA'||composer.tagName==='INPUT'){
                  const proto=composer.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
                  const desc=Object.getOwnPropertyDescriptor(proto,'value');
                  if(desc?.set) desc.set.call(composer,text); else composer.value=text;
                  composer.dispatchEvent(new InputEvent('input',{bubbles:true,composed:true,inputType:'insertText',data:text}));
                  composer.dispatchEvent(new Event('change',{bubbles:true,composed:true}));
                  method='NATIVE_VALUE_SETTER';
                } else {
                  const sel=window.getSelection(); const range=document.createRange();
                  range.selectNodeContents(composer); sel.removeAllRanges(); sel.addRange(range);
                  composer.dispatchEvent(new InputEvent('beforeinput',{bubbles:true,composed:true,inputType:'insertText',data:text}));
                  const inserted=document.execCommand('insertText',false,text);
                  if(!inserted && !composerText(composer).includes(text.slice(0,Math.min(64,text.length)))) composer.textContent=text;
                  composer.dispatchEvent(new InputEvent('input',{bubbles:true,composed:true,inputType:'insertText',data:text}));
                  composer.dispatchEvent(new Event('change',{bubbles:true,composed:true}));
                  method=inserted?'PAGE_WORLD_EXEC_COMMAND':'PAGE_WORLD_TEXT_CONTENT';
                }
              }catch(e){ return JSON.stringify({ok:false,error:'COMPOSER_ACTUATION_EXCEPTION'}); }
              let send=null;
              for(const sel of sendSelectors){
                for(const el of document.querySelectorAll(sel)){ if(visible(el)){ send=el; break; } }
                if(send) break;
              }
              const aria=send?String(send.getAttribute('aria-disabled')||'').toLowerCase():'';
              const dataDisabled=send?String(send.getAttribute('data-disabled')||'').toLowerCase():'';
              const pointer=send?getComputedStyle(send).pointerEvents:'';
              const sendReady=!!send&&!send.disabled&&aria!=='true'&&dataDisabled!=='true'&&!send.inert&&pointer!=='none';
              return JSON.stringify({ok:true,method,reflected:composerText(composer).includes(text.slice(0,Math.min(64,text.length))),send_found:!!send,send_ready:sendReady,aria_disabled:aria,data_disabled:dataDisabled,pointer_events:pointer});
            })()
        """.trimIndent()
    }

'''
assert s.count(insert_anchor)==1; s=s.replace(insert_anchor,handler+insert_anchor)
main.write_text(s)

bridge=root/'app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt'; b=bridge.read_text()
anchor='''    fun post(origin: String, json: String): Boolean {\n'''
method=r'''    fun executePageWorld(origin: String, script: String, onResult: (String) -> Unit): Boolean {
        if (!OriginPolicy.isBridgeOriginAllowed(origin)) return false
        val currentUrl = webView.url ?: return false
        if (currentUrl != origin && !currentUrl.startsWith("$origin/")) return false
        if (script.isBlank() || script.length > 300_000) return false
        webView.post {
            webView.evaluateJavascript(script) { value -> onResult(value ?: "null") }
        }
        return true
    }

'''
assert b.count(anchor)==1; b=b.replace(anchor,method+anchor); bridge.write_text(b)

provider=root/'app/src/main/assets/nexus/claude_provider_c002.js'; j=provider.read_text()
old="  const CHANNEL='NEXUS_POC022_C9_CLAUDE';\n\n"
new="""  const CHANNEL='NEXUS_POC022_C9_CLAUDE';
  const COMPOSER_SELECTORS=[
    'div[contenteditable="true"][role="textbox"]',
    '[contenteditable="true"][data-placeholder]',
    'div.ProseMirror[contenteditable="true"]',
    'textarea',
    '[contenteditable="true"]'
  ];
  const SEND_SELECTORS=[
    'button[data-testid="chat-input-send"]',
    'button[aria-label*="Send" i]',
    'button[aria-label*="Envoyer" i]',
    'button[data-testid*="send" i]'
  ];
  let uiRequestSequence=0;
  const pendingUiRequests=new Map();

"""
assert j.count(old)==1; j=j.replace(old,new)
old_fc='''  function findComposer(){\n    const selectors=[\n      'div[contenteditable="true"][role="textbox"]',\n      '[contenteditable="true"][data-placeholder]',\n      'div.ProseMirror[contenteditable="true"]',\n      'textarea',\n      '[contenteditable="true"]'\n    ];\n    for(const s of selectors){\n'''
new_fc='''  function findComposer(){\n    for(const s of COMPOSER_SELECTORS){\n'''
assert j.count(old_fc)==1; j=j.replace(old_fc,new_fc)
start=j.index('  function findSendButton(){')
end=j.index('  function isGenerating(){', start)
new_send=r'''  function buttonSemanticState(el){
    if(!el) return {ready:false,reason:'MISSING'};
    const aria=String(el.getAttribute('aria-disabled')||'').toLowerCase();
    const dataDisabled=String(el.getAttribute('data-disabled')||'').toLowerCase();
    const pointer=getComputedStyle(el).pointerEvents;
    const ready=visible(el)&&!el.disabled&&aria!=='true'&&dataDisabled!=='true'&&!el.inert&&pointer!=='none';
    return {ready,aria_disabled:aria,data_disabled:dataDisabled,pointer_events:pointer,disabled:!!el.disabled,inert:!!el.inert};
  }

  function findSendButton(){
    for(const s of SEND_SELECTORS){
      for(const el of document.querySelectorAll(s)){
        if(visible(el)) return el;
      }
    }
    const composer=findComposer();
    if(composer){
      const cr=composer.getBoundingClientRect();
      const form=composer.closest('form');
      const nearby=[];
      for(const el of [...document.querySelectorAll('button')].filter(visible)){
        const r=el.getBoundingClientRect();
        const inZone=(r.right>=cr.left-40 && r.left<=cr.right+220 && r.bottom>=cr.top-100 && r.top<=cr.bottom+140);
        if(!inZone) continue;
        const aria=String(el.getAttribute('aria-label')||'');
        const testid=String(el.getAttribute('data-testid')||'');
        const type=String(el.getAttribute('type')||'').toLowerCase();
        let score=0;
        if(/send|envoyer/i.test(aria)) score+=120;
        if(/send/i.test(testid)) score+=110;
        if(type==='submit') score+=70;
        if(form && form.contains(el)) score+=80;
        if(el.querySelector('svg')) score+=30;
        score+=Math.max(0,40-Math.abs(r.right-cr.right)/10);
        if(score>0) nearby.push({el,score});
      }
      nearby.sort((a,b)=>b.score-a.score);
      if(nearby.length) return nearby[0].el;
    }
    return null;
  }

  async function requestPageWorldComposerActuation(bridgeRunId,prompt,timeout=8000){
    const requestId='UI018_'+Date.now().toString(36)+'_'+(++uiRequestSequence).toString(36);
    let timer;
    const wait=new Promise((resolve,reject)=>{
      timer=setTimeout(()=>{ pendingUiRequests.delete(requestId); reject(new Error('PROVIDER_UI_ACTUATE_TIMEOUT')); },timeout);
      pendingUiRequests.set(requestId,(result)=>{ clearTimeout(timer); pendingUiRequests.delete(requestId); resolve(result); });
    });
    await nativeSend({
      channel:CHANNEL,type:'PROVIDER_UI_ACTUATE',bridge_run_id:bridgeRunId,request_id:requestId,
      action:'SET_COMPOSER_TEXT',text:prompt,composer_selectors:COMPOSER_SELECTORS,send_selectors:SEND_SELECTORS
    });
    return wait;
  }

'''
j=j[:start]+new_send+j[end:]
start=j.index('  async function waitForSendReady(composer,timeout=15000){')
end=j.index('  function promptSubmissionSignal(envelope){',start)
new_wait=r'''  async function waitForSendReady(composer,timeout=15000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const btn=findSendButton();
      if(btn && composerText(composer).trim().length>20 && buttonSemanticState(btn).ready) return btn;
      await new Promise(r=>setTimeout(r,250));
    }
    return null;
  }

  async function ensureComposerStateSynchronized(bridgeRunId,envelope,composer,prompt){
    let send=await waitForSendReady(composer,1500);
    if(send){
      await progress(bridgeRunId,'PROVIDER_COMPOSER_SYNC_PASS__ISOLATED_WORLD');
      return {composer,send,mode:'ISOLATED_WORLD'};
    }
    const before=buttonSemanticState(findSendButton());
    await progress(bridgeRunId,'PROVIDER_COMPOSER_SYNC_FALLBACK__PAGE_WORLD');
    const pageResult=await requestPageWorldComposerActuation(bridgeRunId,prompt);
    if(!pageResult || pageResult.ok!==true || pageResult.reflected!==true){
      throw new Error('CLAUDE_COMPOSER_STATE_NOT_SYNCHRONIZED__PAGE_WORLD_ACTUATION_FAILED');
    }
    composer=findComposer();
    if(!composer) throw new Error('CLAUDE_COMPOSER_STATE_NOT_SYNCHRONIZED__COMPOSER_LOST');
    send=await waitForSendReady(composer,8000);
    if(!send){
      const after=buttonSemanticState(findSendButton());
      throw new Error('CLAUDE_COMPOSER_STATE_NOT_SYNCHRONIZED__SEND_NOT_SEMANTICALLY_ACTIVE__before='+JSON.stringify(before)+'__after='+JSON.stringify(after));
    }
    await progress(bridgeRunId,'PROVIDER_COMPOSER_SYNC_PASS__PAGE_WORLD_'+String(pageResult.method||'UNKNOWN'));
    return {composer,send,mode:'PAGE_WORLD'};
  }

'''
j=j[:start]+new_wait+j[end:]
old_exec="""      const prompt=buildPrompt(envelope);
      setComposerText(composer,prompt);
      const turnBaseline=turnGenerationSnapshot(envelope);
      await progress(bridgeRunId,'CLAUDE_TURN_BASELINE__'+compactTurnDiag(turnBaseline));
      let send=await waitForSendReady(composer);

      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');
"""
new_exec="""      const prompt=buildPrompt(envelope);
      setComposerText(composer,prompt);
      const synchronized=await ensureComposerStateSynchronized(bridgeRunId,envelope,composer,prompt);
      const turnBaseline=turnGenerationSnapshot(envelope);
      await progress(bridgeRunId,'CLAUDE_TURN_BASELINE__'+compactTurnDiag(turnBaseline));
      let send=synchronized.send;

      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');
"""
assert j.count(old_exec)==1; j=j.replace(old_exec,new_exec)
old_retry="""        send=findSendButton();
        if(!send) throw new Error('CLAUDE_SEND_BUTTON_NOT_READY_ON_RETRY');
        send.focus();
"""
new_retry="""        send=findSendButton();
        if(!send || !buttonSemanticState(send).ready) throw new Error('CLAUDE_SEND_BUTTON_NOT_READY_ON_RETRY');
        send.focus();
"""
assert j.count(old_retry)==1; j=j.replace(old_retry,new_retry)
old_handler="""  nativeOnMessage((msg,sender,sendResponse)=>{
    if(!msg || msg.channel!==CHANNEL || msg.type!=='EXECUTE_JOB') return;
"""
new_handler="""  nativeOnMessage((msg,sender,sendResponse)=>{
    if(!msg || msg.channel!==CHANNEL) return;
    if(msg.type==='PROVIDER_UI_ACTUATE_RESULT'){
      if(msg.bridge_run_id && msg.request_id){
        const resolve=pendingUiRequests.get(msg.request_id);
        if(resolve) resolve(msg.result||{ok:false,error:'EMPTY_UI_ACTUATE_RESULT'});
      }
      return;
    }
    if(msg.type!=='EXECUTE_JOB') return;
"""
assert j.count(old_handler)==1; j=j.replace(old_handler,new_handler)
provider.write_text(j)
