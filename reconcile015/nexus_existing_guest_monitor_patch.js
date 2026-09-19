'use strict';

(function(){
  const PATCH_ID='NEXUS_C003_EXISTING_GUEST_MONITOR_DEMO_001';
  if(window.__NEXUS_C003_EXISTING_GUEST_MONITOR_PATCH__) return;
  window.__NEXUS_C003_EXISTING_GUEST_MONITOR_PATCH__=PATCH_ID;

  function safeText(detail){
    const s=String(detail||'').replace(/^Error:\s*/,'');
    if(/NOT_AUTHENTICATED|SESSION_NOT_AUTHENTICATED/i.test(s)) return 'La session du LLM sélectionné n’est pas authentifiée.';
    if(/TAB_NOT_FOUND/i.test(s)) return 'L’onglet du LLM sélectionné n’est pas ouvert.';
    if(/TIMEOUT/i.test(s)) return 'Le LLM n’a pas renvoyé de résultat dans le délai prévu.';
    if(/CORRELATION|MISMATCH|FINGERPRINT/i.test(s)) return 'Le résultat reçu ne correspond pas exactement à la demande envoyée.';
    if(/RESULT_PACK/i.test(s)) return 'Le résultat reçu ne respecte pas le format attendu par NEXUS.';
    if(/ANOTHER_V001_JOB_ACTIVE/i.test(s)) return 'Une autre analyse NEXUS est déjà en cours.';
    if(/BRIDGE_UNAVAILABLE|AUTHORIZED_CLIENT_BRIDGE_UNAVAILABLE/i.test(s)) return 'Le lien local entre NEXUS et le LLM n’est pas disponible.';
    return s || 'Le parcours observé n’a pas pu être validé.';
  }

  function injectCss(){
    if(document.getElementById('nexus-existing-guest-monitor-style')) return;
    const style=document.createElement('style');
    style.id='nexus-existing-guest-monitor-style';
    style.textContent=`
      .nxmon{margin-top:12px;border:1px solid #d8e2ea;background:#fff;border-radius:14px;padding:10px 12px;position:relative;overflow:visible}
      .nxmon:before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:#2f6f91;border-radius:14px 0 0 14px}
      .nxmon-line{display:flex;align-items:center;gap:12px;overflow-x:auto;white-space:nowrap;scrollbar-width:thin}
      .nxmon-badge{font-size:9px;font-weight:850;letter-spacing:.06em;color:#607183;border:1px solid #dce4eb;border-radius:999px;padding:5px 8px;background:#f8fafc;flex:none}
      .nxmon-state,.nxmon-diagnostic{font-size:11px;font-weight:850;color:#243a4b;flex:none}
      .nxmon-visual{display:flex;align-items:center;gap:9px;flex:none;margin-left:auto}
      .nxmon-end{display:flex;align-items:center;gap:6px}.nxmon-light{width:13px;height:13px;border-radius:50%;background:#b7c3ce;transition:background .12s ease,box-shadow .12s ease}.nxmon-name{font-size:10px;font-weight:900;color:#43576a}
      .nxmon-end.active .nxmon-light{background:#3382c3;box-shadow:0 0 8px rgba(51,130,195,.35)}.nxmon-end.ok .nxmon-light{background:#2e9b54}.nxmon-end.warn .nxmon-light{background:#d29a27}.nxmon-end.fail .nxmon-light{background:#d94b4b}
      .nxmon-route{display:flex;align-items:center;min-width:190px;justify-content:center}.nxmon-arrows{display:flex;gap:7px}.nxmon-arrow{font-size:16px;font-weight:900;line-height:1;color:#d9e0e6;transition:color .05s linear,transform .05s linear}.nxmon-arrow.hot{color:#18242d}.nxmon-route.returning .nxmon-arrow{transform:rotate(180deg)}
      .nxmon-info-wrap{position:relative;display:inline-flex;align-items:center;gap:5px}.nxmon-info{display:none;border:0;background:transparent;padding:0;color:#a63636;font-size:14px;line-height:1;cursor:pointer}.nxmon-info.show{display:inline-flex}.nxmon-tip{display:none;position:absolute;z-index:2147483646;right:0;top:calc(100% + 8px);width:min(330px,78vw);white-space:normal;background:#172434;color:#fff;border-radius:10px;padding:10px 11px;box-shadow:0 10px 28px rgba(0,0,0,.22);font-size:11px;line-height:1.45}.nxmon-tip.open{display:block}.nxmon-tip strong{display:block;margin-bottom:4px}
      @media(max-width:720px){.nxmon{padding:9px 8px}.nxmon-line{gap:9px}.nxmon-badge{font-size:8px}.nxmon-state,.nxmon-diagnostic{font-size:10px}.nxmon-route{min-width:150px}.nxmon-arrow{font-size:14px}.nxmon-light{width:11px;height:11px}.nxmon-name{font-size:9px}}
    `;
    (document.head||document.documentElement).appendChild(style);
  }

  function injectUi(){
    if(document.getElementById('nexusExchangeMonitor')) return true;
    const status=document.getElementById('promptStatus');
    if(!status||!status.parentNode) return false;
    const box=document.createElement('div');
    box.id='nexusExchangeMonitor';
    box.className='nxmon';
    box.setAttribute('aria-live','polite');
    box.setAttribute('aria-label','Surveillance des échanges NEXUS et LLM');
    box.innerHTML=`<div class="nxmon-line">
      <span class="nxmon-badge">SURVEILLANCE ACTIVE</span>
      <span id="nxmonState" class="nxmon-state">En attente</span>
      <span class="nxmon-info-wrap"><span id="nxmonDiagnostic" class="nxmon-diagnostic">Prêt</span><button id="nxmonInfo" class="nxmon-info" type="button" aria-label="Détail de l’erreur" aria-expanded="false">ⓘ</button><span id="nxmonTip" class="nxmon-tip" role="tooltip"><strong>Erreur détectée</strong><span id="nxmonTipText">Le parcours observé n’a pas pu être validé.</span></span></span>
      <span class="nxmon-visual" aria-hidden="true">
        <span id="nxmonNexus" class="nxmon-end"><span class="nxmon-light"></span><span class="nxmon-name">NEXUS</span></span>
        <span id="nxmonRoute" class="nxmon-route"><span class="nxmon-arrows"><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span><span class="nxmon-arrow">›</span></span></span>
        <span id="nxmonLlm" class="nxmon-end"><span class="nxmon-light"></span><span class="nxmon-name">LLM</span></span>
      </span>
    </div>`;
    status.parentNode.insertBefore(box,status);
    return true;
  }

  const Monitor=(function(){
    let timer=null;
    const $=id=>document.getElementById(id);
    const arrows=()=>Array.from(document.querySelectorAll('#nexusExchangeMonitor .nxmon-arrow'));
    function light(id,kind){const e=$(id);if(!e)return;e.classList.remove('active','ok','warn','fail');if(kind)e.classList.add(kind)}
    function clear(){if(timer){clearInterval(timer);timer=null;}arrows().forEach(a=>a.classList.remove('hot'))}
    function route(kind){clear();const r=$('nxmonRoute'),a=arrows();if(!r||!a.length)return;r.className='nxmon-route '+kind;let i=kind==='returning'?a.length-1:0;const step=()=>{a.forEach((x,j)=>x.classList.toggle('hot',j===i));i+=kind==='returning'?-1:1;if(i>=a.length)i=0;if(i<0)i=a.length-1};step();timer=setInterval(step,80)}
    function text(state,diag){if($('nxmonState'))$('nxmonState').textContent=state;if($('nxmonDiagnostic'))$('nxmonDiagnostic').textContent=diag}
    function info(show,detail){const b=$('nxmonInfo'),t=$('nxmonTip');if(b){b.classList.toggle('show',!!show);b.setAttribute('aria-expanded','false')}if(t)t.classList.remove('open');if($('nxmonTipText'))$('nxmonTipText').textContent=safeText(detail)}
    function reset(){clear();light('nxmonNexus','');light('nxmonLlm','');text('En attente','Prêt');info(false,'')}
    function preparing(){clear();light('nxmonNexus','active');light('nxmonLlm','');text('Préparation','Surveillance active');info(false,'')}
    function outbound(){light('nxmonNexus','active');light('nxmonLlm','');route('outbound');text('NEXUS vers LLM','Surveillance active');info(false,'')}
    function provider(){clear();light('nxmonNexus','');light('nxmonLlm','active');text('Traitement LLM','Surveillance active');info(false,'')}
    function returning(){light('nxmonNexus','active');light('nxmonLlm','ok');route('returning');text('LLM vers NEXUS','Vérification en cours');info(false,'')}
    function pass(){clear();light('nxmonNexus','ok');light('nxmonLlm','ok');text('Terminé','Échange conforme');info(false,'')}
    function fail(detail){clear();light('nxmonNexus','fail');light('nxmonLlm','fail');text('Interrompu','Erreur détectée');info(true,detail)}
    function bind(){const b=$('nxmonInfo'),t=$('nxmonTip');if(!b||b.dataset.bound)return;b.dataset.bound='1';b.addEventListener('click',e=>{e.stopPropagation();const open=!t.classList.contains('open');t.classList.toggle('open',open);b.setAttribute('aria-expanded',String(open))});document.addEventListener('click',()=>{if(t)t.classList.remove('open');if(b)b.setAttribute('aria-expanded','false')})}
    return {reset,preparing,outbound,provider,returning,pass,fail,bind};
  })();
  window.NexusExchangeMonitor=Monitor;

  function observeBridge(){
    const CHANNEL='NEXUS_CLIENT_APP_BRIDGE_V0.1';
    window.addEventListener('message',function(ev){
      if(ev.source!==window||!ev.data||ev.data.channel!==CHANNEL) return;
      const t=String(ev.data.type||'');
      if(t==='NEXUS_BRIDGE_DISPATCH') Monitor.outbound();
      else if(t==='NEXUS_BRIDGE_DISPATCH_RESULT'){
        const r=ev.data.response;
        if(r&&r.ok===true&&r.ack&&r.ack.status==='ACCEPTED') Monitor.provider();
        else Monitor.fail(r&&r.error||'Envoi au LLM refusé.');
      }else if(t==='NEXUS_BRIDGE_RESULT_GET_RESULT'){
        const r=ev.data.response;
        if(r&&r.ok===true&&r.state==='TERMINAL') Monitor.returning();
        else if(r&&r.ok===false) Monitor.fail(r.error||'Retour LLM non disponible.');
      }
    },true);
  }

  async function runConnected(){
    try{
      if(typeof sessionToken==='undefined'||!sessionToken){document.getElementById('promptStatus').textContent='Session invitée absente. Reconnectez-vous.';Monitor.fail('La session Guest NEXUS est absente.');return;}
      const q=String((document.getElementById('prompt')||{}).value||'').trim();
      if(!q){document.getElementById('promptStatus').textContent='Saisissez une demande.';return;}
      const tfEl=document.getElementById('analysisTimeframe');
      const timeframe=String(tfEl?tfEl.value:'').trim();
      if(timeframe.length>240){document.getElementById('promptStatus').textContent='Période analysée trop longue.';return;}
      const provider=String((document.getElementById('llmProvider')||{}).value||'CHATGPT');
      if(!['CHATGPT','CLAUDE'].includes(provider)){const msg='Pour cette démonstration réelle, choisissez ChatGPT ou Claude.';document.getElementById('promptStatus').textContent=msg;Monitor.fail(msg);return;}
      const model=String((document.getElementById('llmModel')||{}).value||'').trim();
      if(typeof runNexusTurn!=='function'||typeof executeNexusConnectedBridgeV1!=='function'){const msg='Cette page Guest ne contient pas le chemin automatisé C003 attendu.';document.getElementById('promptStatus').textContent=msg;Monitor.fail(msg);return;}

      currentMode='ANALYST';currentPrompt=q;currentAnalysisTimeframe=timeframe;currentRequestId='';currentVerdict='';currentSources=[];currentAnalysisId='';currentAnswer='';currentHandoff='';currentProvider=provider;currentModel=model;
      const archiveBtn=document.getElementById('archiveResultBtn');if(archiveBtn)archiveBtn.classList.add('hidden');
      const pdfBtn=document.getElementById('pdfResultBtn');if(pdfBtn)pdfBtn.classList.add('hidden');
      const handoff=document.getElementById('handoffPackage');if(handoff)handoff.value='';
      const external=document.getElementById('externalResult');if(external)external.value='';
      document.getElementById('promptStatus').textContent='Exécution réelle NEXUS → '+provider+' → NEXUS…';
      Monitor.preparing();

      const result=await runNexusTurn({mode:'ANALYST',subjectId:String(currentSubjectId||''),userInput:q,analysisTimeframe:timeframe},{executionMode:'CONNECTED',connectedProvider:provider,connectedModel:model,externalResearch:false});
      if(!result||!result.ok){
        const code=result&&result.error?String(result.error.code||'TURN_FAILED'):'TURN_FAILED';
        const status=result&&result.turn?String(result.turn.status||'FAILED'):'FAILED';
        const msg='Exécution arrêtée : '+code;
        document.getElementById('promptStatus').textContent=msg;
        Monitor.fail(msg+' ('+status+')');
        return result;
      }
      const analysis=result.analysis||{},subject=result.subject||null,turn=result.turn||{};
      currentAnalysisId=String(analysis.id||'');currentRequestId=String(turn.requestId||analysis.requestId||'');currentAnswer=String(analysis.response||'');currentVerdict=String(analysis.verdict||'');currentSources=Array.isArray(analysis.sources)?analysis.sources:[];currentProvider=String(analysis.provider||provider);currentModel=String(analysis.model||model);
      if(subject){currentSubjectId=String(subject.id||currentSubjectId||'');currentSubjectSnapshot={...subject};currentResumeSourceAnalysisId=currentAnalysisId;currentResumeSourceSnapshot={...analysis};}
      if(typeof renderPromptResult==='function') renderPromptResult({answer:currentAnswer,verdict:currentVerdict,sources:currentSources,mapRequested:!!analysis.map,mapState:'NEXUS_TURN_V1_CONNECTED'});
      if(archiveBtn)archiveBtn.classList.remove('hidden');if(pdfBtn)pdfBtn.classList.add('hidden');
      if(typeof renderLocalWorkspace==='function') await renderLocalWorkspace();
      const turnCount=subject?Number(subject.turnCount||0):'';
      document.getElementById('promptStatus').textContent='Échange conforme · résultat reçu et validé'+(turnCount!==''?' · tour '+turnCount:'')+'.';
      Monitor.pass();
      return result;
    }catch(e){
      const detail=String(e&&e.message||e);
      const st=document.getElementById('promptStatus');if(st)st.textContent='Exécution arrêtée : '+safeText(detail);
      Monitor.fail(detail);
      return {ok:false,error:{code:'CONNECTED_DEMO_EXCEPTION',detail}};
    }
  }

  function patchNominalAction(){
    if(typeof window.executeNominalNexusRequest!=='function') return false;
    if(window.executeNominalNexusRequest.__nexusMonitorPatched) return true;
    const original=window.executeNominalNexusRequest;
    const patched=async function(){
      const mode=String((document.getElementById('workMode')||{}).value||window.currentMode||'');
      if(mode==='FACTCHECK') return original.apply(this,arguments);
      if(mode!=='ANALYST') return original.apply(this,arguments);
      return runConnected();
    };
    patched.__nexusMonitorPatched=true;
    patched.__nexusOriginal=original;
    window.executeNominalNexusRequest=patched;
    return true;
  }

  function boot(){
    const isGuest=!!(document.getElementById('viewApp')&&document.getElementById('nexusPrimaryActionBtn')&&document.getElementById('promptStatus'));
    if(!isGuest) return false;
    injectCss();injectUi();Monitor.bind();Monitor.reset();observeBridge();
    let tries=0;
    const timer=setInterval(()=>{tries++;if(patchNominalAction()||tries>60)clearInterval(timer)},100);
    return true;
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
