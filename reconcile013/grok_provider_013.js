'use strict';

(function(){
  const CHANNEL='NEXUS_V007_GROK_013';
  const NATIVE=globalThis.NexusNativeC002;
  let badge=null, running=false, lastStableAuthState=null;

  async function nativeSend(payload){
    if(!NATIVE||typeof NATIVE.postMessage!=='function') throw new Error('ANDROID_NATIVE_BRIDGE_UNAVAILABLE');
    NATIVE.postMessage(JSON.stringify(payload));
    return {ok:true};
  }
  function nativeOnMessage(handler){
    if(!NATIVE||typeof NATIVE.addEventListener!=='function') throw new Error('ANDROID_NATIVE_BRIDGE_UNAVAILABLE');
    NATIVE.addEventListener('message',(event)=>{
      let msg; try{msg=JSON.parse(String(event.data||''));}catch(_){return;}
      const sendResponse=(response)=>nativeSend({channel:CHANNEL,type:'PROVIDER_ACK',bridge_run_id:msg.bridge_run_id,response}).catch(()=>{});
      handler(msg,null,sendResponse);
    });
  }
  function visible(el){
    if(!el||!el.isConnected) return false;
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0) return false;
    const r=el.getBoundingClientRect();
    return r.width>0&&r.height>0;
  }
  function ensureBadge(){
    if(badge&&badge.isConnected) return badge;
    badge=document.createElement('div');
    badge.id='nexus-v007-grok-013-badge';
    badge.style.cssText='position:fixed;right:8px;top:8px;z-index:2147483647;max-width:560px;padding:8px 10px;background:#fff;color:#111;border:2px solid #111;border-radius:8px;font:11px/1.35 system-ui,sans-serif;box-shadow:0 3px 14px rgba(0,0,0,.18)';
    (document.body||document.documentElement).appendChild(badge);
    return badge;
  }
  function show(t){ensureBadge().textContent='NEXUS GROK 013 — '+t;}
  function norm(t){return String(t||'').replace(/\s+/g,' ').trim().toLowerCase();}

  function findComposer(){
    const selectors=['textarea','[contenteditable="true"][role="textbox"]','[contenteditable="true"]','[role="textbox"]'];
    for(const s of selectors){for(const el of document.querySelectorAll(s)){if(visible(el)) return el;}}
    return null;
  }
  function detectAuth(){
    const composer=findComposer();
    const loginRx=/(log in|login|sign in|sign up|se connecter|connexion|inscription)/i;
    const negatives=[];
    for(const el of [...document.querySelectorAll('button,a')].filter(visible)){
      const t=norm([el.getAttribute('aria-label'),el.getAttribute('title'),el.innerText,el.textContent].filter(Boolean).join(' '));
      if(loginRx.test(t)&&t.length<90) negatives.push(t);
    }
    let state='UNKNOWN',reason='NO_STABLE_GROK_SIGNAL';
    if(composer&&negatives.length===0){state='AUTHENTICATED';reason='VISIBLE_GROK_COMPOSER_AND_NO_LOGIN_ACTION';lastStableAuthState=state;}
    else if(!composer&&negatives.length>0){state='UNAUTHENTICATED';reason='VISIBLE_LOGIN_ACTION_AND_NO_GROK_COMPOSER';lastStableAuthState=state;}
    else if(composer){state='COMPOSER_READY_WITH_AMBIGUOUS_LOGIN_UI';reason='VISIBLE_GROK_COMPOSER_WITH_LOGIN_ACTION';}
    else if(lastStableAuthState){state=lastStableAuthState;reason='LAST_STABLE_AUTH_SIGNAL_RETAINED';}
    return {state,reason,observed_at:new Date().toISOString(),evidence:{composer:!!composer,negative_count:negatives.length}};
  }
  async function publishStatus(){const s=detectAuth();if(!running)show('AUTH: '+s.state+' — '+s.reason);try{await nativeSend({channel:CHANNEL,type:'GROK_STATUS',status:s});}catch(_){}}
  function composerText(el){if(!el)return '';if('value' in el&&typeof el.value==='string')return el.value;return el.innerText||el.textContent||'';}
  function setComposerText(el,text){
    el.focus();
    if(el.tagName==='TEXTAREA'||el.tagName==='INPUT'){
      const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
      const desc=Object.getOwnPropertyDescriptor(proto,'value');
      if(desc&&desc.set)desc.set.call(el,text);else el.value=text;
      el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return;
    }
    try{const sel=window.getSelection(),range=document.createRange();range.selectNodeContents(el);sel.removeAllRanges();sel.addRange(range);document.execCommand('insertText',false,text);}catch(_){el.textContent=text;}
    try{el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:text}));}catch(_){el.dispatchEvent(new Event('input',{bubbles:true}));}
  }
  function findSendButton(){
    const selectors=['button[aria-label*="send" i]','button[aria-label*="submit" i]','button[aria-label*="envoyer" i]','button[data-testid*="send" i]','button[type="submit"]'];
    for(const s of selectors){for(const el of document.querySelectorAll(s)){if(visible(el)&&!el.disabled&&el.getAttribute('aria-disabled')!=='true')return el;}}
    return null;
  }
  function responseNodes(){
    const selectors=['[data-message-author-role="assistant"]','[data-testid*="assistant" i]','article','main [class*="message" i]','main [class*="response" i]'];
    const seen=new Set(),out=[];
    for(const s of selectors){for(const el of document.querySelectorAll(s)){if(!visible(el)||seen.has(el))continue;const txt=String(el.innerText||el.textContent||'').trim();if(txt.length<2)continue;seen.add(el);out.push(el);}}
    return out;
  }
  function parseCompleteResultCandidate(text){
    const raw=String(text||'').trim();if(!raw)return null;
    const candidates=[raw];
    const first=raw.indexOf('{'),last=raw.lastIndexOf('}');
    if(first>=0&&last>first)candidates.push(raw.slice(first,last+1));
    for(const candidate of candidates){try{const parsed=JSON.parse(candidate);if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))continue;const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];if(required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k)))return{parsed,normalized_text:candidate};}catch(_){}}
    return null;
  }
  function buildPrompt(envelope){
    const researchPolicy=String(envelope.research_policy||'');
    if(!['FORBIDDEN','ALLOWED','REQUIRED','REQUIRED_IF_STALE'].includes(researchPolicy))throw new Error('EXECUTION_RESEARCH_POLICY_INVALID');
    return ['You are executing a NEXUS read-only user analysis in this authenticated Grok browser session.','','MANDATORY EXECUTION RULES:','- Answer the QUESTION directly using your current model knowledge and the supplied frozen package metadata.','- Follow the resolved M024 execution policy carried by the envelope.',(researchPolicy==='FORBIDDEN'?'- Research policy FORBIDDEN: do not browse externally.':researchPolicy==='REQUIRED'?'- Research policy REQUIRED: perform required external research and preserve source traceability.':researchPolicy==='REQUIRED_IF_STALE'?'- Research policy REQUIRED_IF_STALE: research when freshness/source gaps require it.':'- Research policy ALLOWED: external research may be used when useful and permitted.'),'- Do NOT canonicalize anything and do NOT mutate any NEXUS state.','- Return exactly ONE JSON object and nothing else.','- Preserve expected Result Pack static fields; replace answer with your substantive answer.','- For result_pack.model.provider use "xAI".','- For result_pack.model.model use "Grok UI session — exact backend model not exposed by bridge".','','QUESTION:',envelope.question,'','FROZEN PACKAGE:',JSON.stringify(envelope.frozen_package,null,2),'','Generate the completed Result Pack now.'].join('\n');
  }
  async function progress(id,status){show(status);try{await nativeSend({channel:CHANNEL,type:'PROVIDER_PROGRESS',bridge_run_id:id,job_status:status});}catch(_){}}
  async function waitForSendReady(composer,timeout=15000){const deadline=Date.now()+timeout;while(Date.now()<deadline){const btn=findSendButton(),txt=composerText(composer).trim();if(btn&&txt.length>20)return btn;await new Promise(r=>setTimeout(r,250));}throw new Error('GROK_SEND_BUTTON_NOT_READY');}
  async function waitForModelResult(id,beforeCount,timeout=160000){
    const deadline=Date.now()+timeout;let validText='',validSince=0,validParsed=null,lastCount=beforeCount;
    while(Date.now()<deadline){
      const nodes=responseNodes();lastCount=nodes.length;const start=Math.min(beforeCount,nodes.length);
      for(let i=nodes.length-1;i>=start;i--){const txt=String(nodes[i].innerText||nodes[i].textContent||'').trim();const c=parseCompleteResultCandidate(txt);if(!c)continue;if(c.normalized_text===validText){if(!validSince)validSince=Date.now();}else{validText=c.normalized_text;validParsed=c.parsed;validSince=Date.now();await progress(id,'GROK_JSON_COMPLETE_DETECTED');}if(Date.now()-validSince>=5000)return{text:validText,parsed:validParsed,node_count:nodes.length,json_stable_ms:Date.now()-validSince};break;}
      await new Promise(r=>setTimeout(r,400));
    }
    throw new Error('GROK_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__nodes='+String(lastCount));
  }
  async function executeJob(id,envelope){
    if(running)throw new Error('GROK_PROVIDER_ALREADY_RUNNING');running=true;
    try{
      const auth=detectAuth(),composer=findComposer(),manuallyConfirmed=envelope.user_confirmed_connected===true;
      const sessionUsable=auth.state==='AUTHENTICATED'||(manuallyConfirmed&&!!composer);
      if(!sessionUsable)throw new Error('GROK_NOT_AUTHENTICATED:'+auth.state);
      if(envelope.provider_family!=='XAI')throw new Error('PROVIDER_FAMILY_NOT_XAI');
      if(envelope.canonical_rights!=='NONE'||envelope.state_mutation_mode!=='NONE')throw new Error('STATE_MUTATION_FORBIDDEN');
      await progress(id,'GROK_UI_PREPARING');if(!composer)throw new Error('GROK_COMPOSER_NOT_FOUND');
      const beforeCount=responseNodes().length,prompt=buildPrompt(envelope);setComposerText(composer,prompt);const send=await waitForSendReady(composer);
      await progress(id,'GROK_UI_PROMPT_READY');send.focus();send.click();await progress(id,'GROK_UI_PROMPT_CLICKED');
      const result=await waitForModelResult(id,beforeCount);await progress(id,'GROK_UI_RESPONSE_CAPTURED');
      await nativeSend({channel:CHANNEL,type:'PROVIDER_RESULT',bridge_run_id:id,ok:true,result_pack:result.parsed,provider_meta:{ui_origin:location.origin,response_count:result.node_count,json_stable_ms:result.json_stable_ms||null,auth_observation:auth,manual_confirmation_used:manuallyConfirmed,exact_backend_model_exposed:false}});
      show('TERMINAL COMPLETED — résultat renvoyé à NEXUS');
    }catch(err){const code=String((err&&err.message)||err);try{await nativeSend({channel:CHANNEL,type:'PROVIDER_RESULT',bridge_run_id:id,ok:false,error:code});}catch(_){}show('TERMINAL FAILED — '+code);}
    finally{running=false;setTimeout(publishStatus,2000);}
  }
  nativeOnMessage((msg,sender,sendResponse)=>{if(!msg||msg.channel!==CHANNEL||msg.type!=='EXECUTE_JOB')return;if(running){sendResponse({ok:false,error:'GROK_PROVIDER_ALREADY_RUNNING'});return;}sendResponse({ok:true,accepted:true});setTimeout(()=>executeJob(msg.bridge_run_id,msg.envelope),0);});
  publishStatus();setInterval(publishStatus,3000);
  const mo=new MutationObserver(()=>{clearTimeout(mo._t);mo._t=setTimeout(publishStatus,350);});mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true});
  [0,100,300,1000].forEach((delay)=>setTimeout(()=>{nativeSend({channel:CHANNEL,type:'BRIDGE_READY'}).catch(()=>{});},delay));
  console.info('[NEXUS V007 GROK 013] provider bridge active');
})();