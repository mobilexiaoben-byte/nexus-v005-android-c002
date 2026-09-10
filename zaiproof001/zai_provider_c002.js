'use strict';

(function(){
  const CHANNEL='NEXUS_V005_ZAI_001';
  const NATIVE=globalThis.NexusNativeC002;
  let running=false;
  let badge=null;
  let lastStableAuthState=null;

  async function nativeSend(payload){
    if(!NATIVE || typeof NATIVE.postMessage!=='function') throw new Error('ANDROID_NATIVE_BRIDGE_UNAVAILABLE');
    NATIVE.postMessage(JSON.stringify(payload));
    return {ok:true};
  }

  function nativeOnMessage(handler){
    if(!NATIVE || typeof NATIVE.addEventListener!=='function') throw new Error('ANDROID_NATIVE_BRIDGE_UNAVAILABLE');
    NATIVE.addEventListener('message',(event)=>{
      let msg;
      try{ msg=JSON.parse(String(event.data||'')); }catch(_){ return; }
      const sendResponse=(response)=>{
        nativeSend({channel:CHANNEL,type:'PROVIDER_ACK',bridge_run_id:msg.bridge_run_id,response}).catch(()=>{});
      };
      handler(msg,null,sendResponse);
    });
  }

  function visible(el){
    if(!el || !el.isConnected) return false;
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0) return false;
    const r=el.getBoundingClientRect();
    return r.width>0 && r.height>0;
  }

  function ensureBadge(){
    if(badge && badge.isConnected) return badge;
    badge=document.createElement('div');
    badge.id='nexus-v005-zai-proof001-badge';
    badge.style.cssText=[
      'position:fixed','right:8px','top:8px','z-index:2147483647',
      'max-width:560px','padding:8px 10px','background:#fff','color:#111',
      'border:2px solid #111','border-radius:8px','font:11px/1.35 system-ui,sans-serif',
      'box-shadow:0 3px 14px rgba(0,0,0,.18)'
    ].join(';');
    (document.body||document.documentElement).appendChild(badge);
    return badge;
  }

  function show(text){ ensureBadge().textContent='NEXUS Z.AI — '+text; }
  function norm(v){ return String(v||'').replace(/\s+/g,' ').trim().toLowerCase(); }

  function findComposer(){
    const preferred=[
      document.getElementById('chat-input'),
      document.getElementById('chat-textarea'),
      ...document.querySelectorAll('textarea#chat-input,textarea#chat-textarea'),
      ...document.querySelectorAll('[contenteditable="true"][role="textbox"]'),
      ...document.querySelectorAll('textarea'),
      ...document.querySelectorAll('[contenteditable="true"]')
    ].filter(Boolean);
    return preferred.find(visible)||null;
  }

  function composerText(el){
    if(!el) return '';
    if('value' in el && typeof el.value==='string') return el.value;
    return el.innerText||el.textContent||'';
  }

  function detectAuth(){
    const composer=findComposer();
    const loginTexts=['sign in','signin','log in','login','se connecter','connexion'];
    const authActions=[...document.querySelectorAll('button,a,[role="button"]')].filter(visible).map(el=>norm(el.innerText||el.textContent||el.getAttribute('aria-label')||''));
    const visibleLogin=authActions.some(t=>loginTexts.includes(t));
    const skipVisible=authActions.some(t=>t==='skip for now'||t==='passer pour le moment');
    let state='UNKNOWN',reason='NO_STABLE_ZAI_SESSION_SIGNAL';
    if(composer){
      state='AUTHENTICATED';
      reason=visibleLogin?'VISIBLE_ZAI_COMPOSER_SESSION_READY_WITH_ACCOUNT_ACTION':'VISIBLE_ZAI_COMPOSER_SESSION_READY';
      lastStableAuthState='AUTHENTICATED';
    }else if(visibleLogin||skipVisible){
      state='UNAUTHENTICATED';
      reason=skipVisible?'ZAI_AUTH_OR_SKIP_REQUIRED':'VISIBLE_LOGIN_ACTION_AND_NO_ZAI_COMPOSER';
      lastStableAuthState='UNAUTHENTICATED';
    }else if(lastStableAuthState){
      state=lastStableAuthState;
      reason='LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE';
    }
    return {
      state,reason,observed_at:new Date().toISOString(),observed_at_ms:Date.now(),
      evidence:{
        positive:[...(composer?['visible_zai_composer']:[]),...(skipVisible?['skip_for_now_visible']:[])],
        negative:[...(visibleLogin?['visible_login_action']:[])],
        support:['composer_present='+(composer?1:0),'login_action='+(visibleLogin?1:0),'skip_visible='+(skipVisible?1:0)]
      }
    };
  }

  async function publishStatus(){
    const s=detectAuth();
    if(!running) show('AUTH: '+s.state+' — '+s.reason);
    try{ await nativeSend({channel:CHANNEL,type:'ZAI_STATUS',status:s}); }catch(_){}
  }

  function setComposerText(el,text){
    el.focus();
    if(el.tagName==='TEXTAREA'||el.tagName==='INPUT'){
      const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
      const desc=Object.getOwnPropertyDescriptor(proto,'value');
      if(desc?.set) desc.set.call(el,text); else el.value=text;
      el.dispatchEvent(new Event('input',{bubbles:true}));
      el.dispatchEvent(new Event('change',{bubbles:true}));
      return;
    }
    try{
      const sel=window.getSelection();
      const range=document.createRange();
      range.selectNodeContents(el);
      sel.removeAllRanges();
      sel.addRange(range);
      document.execCommand('insertText',false,text);
    }catch(_){
      el.textContent=text;
    }
    try{
      el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));
    }catch(_){
      el.dispatchEvent(new Event('input',{bubbles:true}));
    }
  }

  function findSendButton(){
    const selectors=[
      '#send-message-button',
      'button[data-testid="send-message-button"]',
      'button[aria-label*="Send Message" i]',
      'button[aria-label*="Send" i]',
      'button[aria-label*="Envoyer" i]',
      'form button[type="submit"]'
    ];
    for(const s of selectors){
      for(const el of document.querySelectorAll(s)){
        if(visible(el)&&!el.disabled&&el.getAttribute('aria-disabled')!=='true') return el;
      }
    }
    for(const b of [...document.querySelectorAll('button')].filter(visible)){
      if(b.disabled||b.getAttribute('aria-disabled')==='true') continue;
      const t=norm([b.getAttribute('aria-label'),b.getAttribute('title'),b.innerText,b.textContent].filter(Boolean).join(' '));
      if(/(^|\s)(send|send message|envoyer)(\s|$)/i.test(t)) return b;
    }
    return null;
  }

  function responseNodes(){
    const primary=[...document.querySelectorAll('.chat-assistant')].filter(visible);
    if(primary.length) return primary;
    const second=[...document.querySelectorAll('[data-testid*="assistant-message" i],[data-role="assistant" i]')].filter(visible);
    if(second.length) return second;
    const all=[...document.querySelectorAll('div[id^="message-"],article,[data-message-id]')].filter(visible);
    return all.filter(el=>{
      const t=norm(el.getAttribute('class')||'');
      return t.includes('assistant')||t.includes('response');
    });
  }

  function generating(){
    for(const b of [...document.querySelectorAll('button')].filter(visible)){
      const t=norm([b.getAttribute('aria-label'),b.getAttribute('title'),b.innerText].filter(Boolean).join(' '));
      if(/stop|stop response|arr[eê]ter|interrompre/.test(t)) return true;
    }
    return false;
  }

  function parseCompleteResultCandidate(text){
    const raw=String(text||'').trim();
    if(!raw) return null;
    if(raw.includes('FROZEN PACKAGE:')||raw.includes('MANDATORY EXECUTION RULES:')||raw.includes('Generate the completed Result Pack now.')) return null;
    const candidates=[raw];
    if(raw.startsWith('```')) candidates.push(raw.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim());
    const first=raw.indexOf('{'),last=raw.lastIndexOf('}');
    if(first>=0&&last>first) candidates.push(raw.slice(first,last+1));
    for(const candidate of candidates){
      try{
        const parsed=JSON.parse(candidate);
        if(!parsed||typeof parsed!=='object'||Array.isArray(parsed)) continue;
        const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
        if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
        return {parsed,normalized_text:candidate};
      }catch(_){}
    }
    return null;
  }

  function buildPrompt(envelope){
    return [
      'You are executing a NEXUS read-only post-response audit in this Z.ai browser session.',
      '',
      'MANDATORY EXECUTION RULES:',
      '- Use only the supplied frozen package below.',
      '- Do NOT browse the web and do NOT perform external research.',
      '- Do NOT rewrite Analysis A.',
      '- Do NOT canonicalize anything and do NOT mutate any NEXUS state.',
      '- Return exactly ONE JSON object and nothing else.',
      '- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.',
      '- For result_pack.model.provider use "Z.ai".',
      '- For result_pack.model.model use "Z.ai UI session — exact backend model not exposed by bridge".',
      '- Do not claim an exact internal model version.',
      '',
      'QUESTION:',envelope.question,'',
      'FROZEN PACKAGE:',JSON.stringify(envelope.frozen_package,null,2),'',
      'Generate the completed Result Pack now.'
    ].join('\n');
  }

  async function progress(bridgeRunId,status){
    show(status);
    try{ await nativeSend({channel:CHANNEL,type:'PROVIDER_PROGRESS',bridge_run_id:bridgeRunId,job_status:status}); }catch(_){}
  }

  async function waitForSendReady(composer,timeout=15000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const btn=findSendButton();
      const txt=composerText(composer).trim();
      if(btn&&txt.length>20) return btn;
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('ZAI_SEND_BUTTON_NOT_READY');
  }

  async function waitForSubmissionEstablished(envelope,beforeCount,timeout=12000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const composer=findComposer();
      const text=composerText(composer).trim();
      const promptGone=!text.includes(envelope.context_pack_id)&&!text.includes('Generate the completed Result Pack now.');
      const responseStarted=responseNodes().length>beforeCount||generating();
      if(promptGone||responseStarted) return {prompt_gone:promptGone,response_started:responseStarted};
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('ZAI_PROMPT_SUBMISSION_NOT_ESTABLISHED');
  }

  async function waitForModelResult(bridgeRunId,beforeCount,timeout=160000){
    const deadline=Date.now()+timeout;
    let validText='',validSince=0,validParsed=null,lastCount=beforeCount;
    while(Date.now()<deadline){
      const nodes=responseNodes();
      lastCount=nodes.length;
      const start=Math.min(beforeCount,nodes.length);
      for(let i=nodes.length-1;i>=start;i--){
        const txt=String(nodes[i].innerText||nodes[i].textContent||'').trim();
        const candidate=parseCompleteResultCandidate(txt);
        if(!candidate) continue;
        if(candidate.normalized_text===validText){ if(!validSince) validSince=Date.now(); }
        else { validText=candidate.normalized_text; validParsed=candidate.parsed; validSince=Date.now(); await progress(bridgeRunId,'ZAI_JSON_COMPLETE_DETECTED'); }
        if(Date.now()-validSince>=5000){
          return {text:validText,parsed:validParsed,node_count:nodes.length,json_stable_ms:Date.now()-validSince};
        }
        break;
      }
      await new Promise(r=>setTimeout(r,400));
    }
    throw new Error('ZAI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__response_nodes='+String(lastCount));
  }

  async function executeJob(bridgeRunId,envelope){
    if(running) throw new Error('ZAI_PROVIDER_ALREADY_RUNNING');
    running=true;
    try{
      const auth=detectAuth();
      if(auth.state!=='AUTHENTICATED') throw new Error('ZAI_SESSION_NOT_READY:'+auth.state);
      if(envelope.provider_family!=='ZAI') throw new Error('PROVIDER_FAMILY_NOT_ZAI');
      if(envelope.external_research!==false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');
      if(envelope.canonical_rights!=='NONE'||envelope.state_mutation_mode!=='NONE') throw new Error('STATE_MUTATION_FORBIDDEN');

      await progress(bridgeRunId,'ZAI_UI_PREPARING');
      const composer=findComposer();
      if(!composer) throw new Error('ZAI_COMPOSER_NOT_FOUND');
      const beforeCount=responseNodes().length;
      const prompt=buildPrompt(envelope);
      setComposerText(composer,prompt);
      const send=await waitForSendReady(composer);
      await progress(bridgeRunId,'ZAI_UI_PROMPT_READY');
      send.focus(); send.click();
      await progress(bridgeRunId,'ZAI_UI_PROMPT_CLICKED');
      const submission=await waitForSubmissionEstablished(envelope,beforeCount);
      await progress(bridgeRunId,'ZAI_UI_PROMPT_SENT_CONFIRMED__'+(submission.response_started?'RESPONSE_STARTED':'COMPOSER_CLEARED'));
      const result=await waitForModelResult(bridgeRunId,beforeCount);
      await progress(bridgeRunId,'ZAI_UI_RESPONSE_CAPTURED');
      await nativeSend({
        channel:CHANNEL,type:'PROVIDER_RESULT',bridge_run_id:bridgeRunId,ok:true,result_pack:result.parsed,
        provider_meta:{
          ui_origin:location.origin,
          response_count:result.node_count,
          json_stable_ms:result.json_stable_ms||null,
          completion_rule:'COMPLETE_JSON_REQUIRED__STABLE_5000MS',
          auth_observation:auth,
          exact_backend_model_exposed:false
        }
      });
      show('TERMINAL COMPLETED — résultat renvoyé à NEXUS');
    }catch(err){
      const code=String(err?.message||err);
      try{ await nativeSend({channel:CHANNEL,type:'PROVIDER_RESULT',bridge_run_id:bridgeRunId,ok:false,error:code}); }catch(_){}
      show('TERMINAL FAILED — '+code);
    }finally{
      running=false;
      setTimeout(publishStatus,2000);
    }
  }

  nativeOnMessage((msg,sender,sendResponse)=>{
    if(!msg||msg.channel!==CHANNEL||msg.type!=='EXECUTE_JOB') return;
    if(running){ sendResponse({ok:false,error:'ZAI_PROVIDER_ALREADY_RUNNING'}); return; }
    sendResponse({ok:true,accepted:true});
    setTimeout(()=>executeJob(msg.bridge_run_id,msg.envelope),0);
  });

  publishStatus();
  setInterval(publishStatus,3000);
  const mo=new MutationObserver(()=>{ clearTimeout(mo._t); mo._t=setTimeout(publishStatus,350); });
  mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true});
  console.info('[NEXUS V005 ZAI 001] provider bridge active');
})();
