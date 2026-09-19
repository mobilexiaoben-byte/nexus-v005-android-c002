'use strict';

(function(){
  const CHANNEL='NEXUS_POC022_C8B2R1';

  const NATIVE=globalThis.NexusNativeC002;
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
  let badge;
  let running=false;
  let lastStableAuthState=null;

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
    badge.id='nexus-c8b2r1-chatgpt-badge';
    badge.style.cssText=[
      'position:fixed','right:8px','top:8px','z-index:2147483647',
      'max-width:560px','padding:8px 10px','background:#fff','color:#111',
      'border:2px solid #111','border-radius:8px',
      'font:11px/1.35 system-ui,sans-serif',
      'box-shadow:0 3px 14px rgba(0,0,0,.18)'
    ].join(';');
    (document.body||document.documentElement).appendChild(badge);
    return badge;
  }

  function show(t){ ensureBadge().textContent='NEXUS C8B2R1 — '+t; }

  function detectAuth(){
    const profiles=[...document.querySelectorAll('[data-testid="accounts-profile-button"]')].filter(visible);
    const authTexts=new Set(['se connecter','connexion','log in','login','inscription gratuite',"s'inscrire",'s’inscrire','sign up','signup']);
    const neg=[];
    for(const b of [...document.querySelectorAll('button')].filter(visible)){
      const t=String(b.innerText||b.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
      if(authTexts.has(t)) neg.push(t);
    }
    let state='UNKNOWN', reason='NO_STABLE_RUNTIME_PROVEN_SIGNAL';
    if(profiles.length>0 && neg.length===0){
      state='AUTHENTICATED';
      reason='RUNTIME_PROVEN_PROFILE_BUTTON_PRESENT_AND_LOGIN_SIGNUP_ABSENT';
      lastStableAuthState='AUTHENTICATED';
    }else if(profiles.length===0 && neg.length>0){
      state='UNAUTHENTICATED';
      reason='RUNTIME_PROVEN_LOGIN_SIGNUP_PRESENT_AND_PROFILE_BUTTON_ABSENT';
      lastStableAuthState='UNAUTHENTICATED';
    }else if(profiles.length>0 && neg.length>0){
      reason='CONFLICTING_AUTH_UI_SIGNALS';
    }else if(lastStableAuthState){
      state=lastStableAuthState;
      reason='LAST_STABLE_AUTH_SIGNAL_RETAINED_DURING_TRANSIENT_DOM_STATE';
    }
    return {
      state,reason,
      observed_at:new Date().toISOString(),
      observed_at_ms:Date.now(),
      evidence:{
        positive:profiles.length?['data-testid=accounts-profile-button']:[],
        negative:[...new Set(neg)].map(x=>'visible_auth_action:'+x),
        support:['profile_button_count='+profiles.length]
      }
    };
  }

  async function publishStatus(){
    const s=detectAuth();
    if(!running) show('CHATGPT AUTH: '+s.state);
    try{
      await nativeSend({channel:CHANNEL,type:'CHATGPT_STATUS',status:s});
    }catch(_){}
  }

  function findComposer(){
    const candidates=[
      document.querySelector('#prompt-textarea'),
      document.querySelector('textarea'),
      ...document.querySelectorAll('[contenteditable="true"]')
    ].filter(Boolean);
    return candidates.find(visible) || null;
  }

  function composerText(el){
    if(!el) return '';
    if('value' in el && typeof el.value==='string') return el.value;
    return el.innerText || el.textContent || '';
  }

  function setComposerText(el, text){
    el.focus();

    if(el.tagName==='TEXTAREA' || el.tagName==='INPUT'){
      const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
      const desc=Object.getOwnPropertyDescriptor(proto,'value');
      if(desc?.set) desc.set.call(el,text);
      else el.value=text;
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
    el.dispatchEvent(new InputEvent('input',{
      bubbles:true,
      inputType:'insertText',
      data:text
    }));
  }

  function findSendButton(){
    const selectors=[
      '[data-testid="send-button"]',
      '[data-testid="composer-submit-button"]',
      'button[aria-label="Envoyer un message"]',
      'button[aria-label="Send message"]',
      'button[aria-label*="Envoyer" i]',
      'button[aria-label*="Send" i]'
    ];
    for(const s of selectors){
      const el=document.querySelector(s);
      if(el && visible(el) && !el.disabled) return el;
    }
    return null;
  }

  function assistantNodes(){
    let nodes=[...document.querySelectorAll('[data-message-author-role="assistant"]')];
    if(nodes.length) return nodes;
    nodes=[...document.querySelectorAll('article')].filter(el=>{
      const t=(el.getAttribute('data-turn')||el.getAttribute('data-message-author-role')||'').toLowerCase();
      return t==='assistant';
    });
    return nodes;
  }

  function stripToJson(text){
    let s=String(text||'').trim();
    if(s.startsWith('```')){
      s=s.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim();
    }
    try { return JSON.parse(s); } catch(_){}
    const a=s.indexOf('{'), b=s.lastIndexOf('}');
    if(a>=0 && b>a){
      const sub=s.slice(a,b+1);
      return JSON.parse(sub);
    }
    throw new Error('RESULT_JSON_PARSE_FAILED');
  }

  function buildPrompt(envelope){
    const pack=JSON.stringify(envelope.frozen_package,null,2);
    return [
      'You are executing a NEXUS read-only post-response audit in this authenticated ChatGPT browser session.',
      '',
      'MANDATORY EXECUTION RULES:',
      '- Use only the supplied frozen package below.',
      '- Do NOT browse the web and do NOT perform external research.',
      '- Do NOT rewrite Analysis A.',
      '- Do NOT canonicalize anything and do NOT mutate any NEXUS state.',
      '- Return exactly ONE JSON object and nothing else.',
      '- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.',
      '- For result_pack.model.provider use "OpenAI".',
      '- For result_pack.model.model use "ChatGPT UI session — exact backend model not exposed by bridge".',
      '- Do not claim an exact internal model version.',
      '',
      'QUESTION:',
      envelope.question,
      '',
      'FROZEN PACKAGE:',
      pack,
      '',
      'Generate the completed Result Pack now.'
    ].join('\n');
  }

  async function progress(bridgeRunId,status){
    show(status);
    try{
      await nativeSend({
        channel:CHANNEL,
        type:'PROVIDER_PROGRESS',
        bridge_run_id:bridgeRunId,
        job_status:status
      });
    }catch(_){}
  }

  async function waitForSendReady(composer, timeout=12000){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const btn=findSendButton();
      const txt=composerText(composer).trim();
      if(btn && txt.length>20) return btn;
      await new Promise(r=>setTimeout(r,250));
    }
    throw new Error('CHATGPT_SEND_BUTTON_NOT_READY');
  }

  function parseCompleteResultCandidate(text){
    const raw=String(text||'').trim();
    if(!raw) return null;

    const candidates=[raw];
    if(raw.startsWith('```')){
      candidates.push(raw.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim());
    }
    const first=raw.indexOf('{');
    const last=raw.lastIndexOf('}');
    if(first>=0 && last>first) candidates.push(raw.slice(first,last+1));

    for(const candidate of candidates){
      try{
        const parsed=JSON.parse(candidate);
        if(!parsed || typeof parsed!=='object' || Array.isArray(parsed)) continue;
        const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
        if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
        return {parsed, normalized_text:candidate};
      }catch(_){}
    }
    return null;
  }

  async function waitForAssistantResult(beforeCount, timeout=160000){
    const deadline=Date.now()+timeout;
    let validText='';
    let validSince=0;
    let validParsed=null;
    let lastNodeCount=beforeCount;

    while(Date.now()<deadline){
      const nodes=assistantNodes();
      lastNodeCount=nodes.length;
      if(nodes.length>beforeCount){
        const node=nodes[nodes.length-1];
        const txt=String(node.innerText||node.textContent||'').trim();
        const candidate=parseCompleteResultCandidate(txt);
        if(candidate){
          if(candidate.normalized_text===validText){
            if(!validSince) validSince=Date.now();
          }else{
            validText=candidate.normalized_text;
            validParsed=candidate.parsed;
            validSince=Date.now();
            show('JSON complet détecté — stabilité en cours');
          }
          if(Date.now()-validSince>=8000){
            return {text:validText,parsed:validParsed,node_count:nodes.length,json_stable_ms:Date.now()-validSince};
          }
        }else{
          validText='';
          validParsed=null;
          validSince=0;
        }
      }
      await new Promise(r=>setTimeout(r,400));
    }
    throw new Error('CHATGPT_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__assistant_nodes='+String(lastNodeCount));
  }

  async function executeJob(bridgeRunId,envelope){
    if(running) throw new Error('CHATGPT_PROVIDER_ALREADY_RUNNING');
    running=true;
    try{
      const auth=detectAuth();
      if(auth.state!=='AUTHENTICATED') throw new Error('CHATGPT_NOT_AUTHENTICATED:'+auth.state);
      if(envelope.provider_family!=='OPENAI') throw new Error('PROVIDER_FAMILY_NOT_OPENAI');
      if(envelope.external_research!==false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');
      if(envelope.canonical_rights!=='NONE'||envelope.state_mutation_mode!=='NONE') throw new Error('STATE_MUTATION_FORBIDDEN');

      await progress(bridgeRunId,'CHATGPT_UI_PREPARING');
      const composer=findComposer();
      if(!composer) throw new Error('CHATGPT_COMPOSER_NOT_FOUND');
      const beforeCount=assistantNodes().length;
      const prompt=buildPrompt(envelope);
      setComposerText(composer,prompt);
      const send=await waitForSendReady(composer);
      await progress(bridgeRunId,'CHATGPT_UI_PROMPT_READY');
      send.click();
      await progress(bridgeRunId,'CHATGPT_UI_PROMPT_SENT');
      const result=await waitForAssistantResult(beforeCount);
      await progress(bridgeRunId,'CHATGPT_UI_RESPONSE_CAPTURED');
      const parsed=result.parsed || stripToJson(result.text);
      await nativeSend({
        channel:CHANNEL,
        type:'PROVIDER_RESULT',
        bridge_run_id:bridgeRunId,
        ok:true,
        result_pack:parsed,
        provider_meta:{
          ui_origin:location.origin,
          assistant_node_count:result.node_count,
          json_stable_ms:result.json_stable_ms || null,
          completion_rule:'COMPLETE_JSON_REQUIRED__STABLE_8000MS',
          auth_observation:auth,
          exact_backend_model_exposed:false
        }
      });
      show('TERMINAL COMPLETED — résultat renvoyé à NEXUS');
    }catch(err){
      const code=String(err?.message||err);
      try{
        await nativeSend({channel:CHANNEL,type:'PROVIDER_RESULT',bridge_run_id:bridgeRunId,ok:false,error:code});
      }catch(_){}
      show('TERMINAL FAILED — '+code);
    }finally{
      running=false;
      setTimeout(publishStatus,2000);
    }
  }

  nativeOnMessage((msg,sender,sendResponse)=>{
    if(!msg || msg.channel!==CHANNEL || msg.type!=='EXECUTE_JOB') return;
    if(running){
      sendResponse({ok:false,error:'CHATGPT_PROVIDER_ALREADY_RUNNING'});
      return;
    }
    sendResponse({ok:true,accepted:true});
    setTimeout(()=>executeJob(msg.bridge_run_id,msg.envelope),0);
    return;
  });

  publishStatus();
  setInterval(publishStatus,3000);
  const mo=new MutationObserver(()=>{
    clearTimeout(mo._t);
    mo._t=setTimeout(publishStatus,350);
  });
  mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true});

  console.info('[NEXUS C8B2R1] real ChatGPT UI provider bridge active');
})();
