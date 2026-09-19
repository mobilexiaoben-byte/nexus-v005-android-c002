'use strict';

(function(){
  const PATCH_ID='U011_DESKTOP_REPORT_PANEL_PATCH_001';
  if(window.__NEXUS_U011_REPORT_PANEL_PATCH__===PATCH_ID) return;
  window.__NEXUS_U011_REPORT_PANEL_PATCH__=PATCH_ID;

  const MAX_LINES=250;
  const lines=[];
  const CHANNELS=new Set([
    'NEXUS_CLIENT_APP_BRIDGE_V0.1',
    'NEXUS_V005_CHATGPT_C002',
    'NEXUS_V005_GEMINI_C002',
    'NEXUS_V005_CLAUDE_C002',
    'NEXUS_V005_ZAI_001',
    'NEXUS_V007_GROK_013'
  ]);

  function clip(value,max){
    return String(value==null?'':value).replace(/[\r\n]+/g,' ').slice(0,max);
  }

  function append(category,detail){
    const row=[new Date().toISOString(),clip(category,80),clip(detail,4000)].join(' | ');
    lines.push(row);
    if(lines.length>MAX_LINES) lines.splice(0,lines.length-MAX_LINES);
    const body=document.getElementById('nexusAdvancedReportBody');
    if(body){
      body.textContent=[
        'Diagnostic avancé NEXUS',
        'V-009 ARCH005 0.1.7.2 — FROZEN / UNMODIFIED',
        'U-011 Desktop — overlay de diagnostic uniquement',
        '',
        ...lines
      ].join('\n');
    }
    const panel=document.getElementById('nexusAdvancedReport');
    if(panel && !panel.hidden) panel.scrollTop=panel.scrollHeight;
  }

  function installCss(){
    if(document.getElementById('nexus-u011-report-panel-style')) return;
    const style=document.createElement('style');
    style.id='nexus-u011-report-panel-style';
    style.textContent=
      '#nexusExchangeMonitor.nxmon-u011-report-host{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:start}' +
      '#nexusExchangeMonitor.nxmon-u011-report-host>.nxmon-line{min-width:0}' +
      '#nexusReportToggle{align-self:center;border:1px solid #ccd7e0;background:#f8fafc;color:#243a4b;border-radius:9px;padding:6px 9px;font-size:10px;font-weight:850;cursor:pointer;white-space:nowrap}' +
      '#nexusReportToggle[aria-expanded="true"]{background:#edf4f8}' +
      '#nexusAdvancedReport{grid-column:1/-1;max-height:min(36vh,320px);overflow-y:auto;overflow-x:auto;border-top:1px solid #dde5eb;margin-top:2px;padding:9px 8px 5px;background:#fbfcfd;scrollbar-width:thin}' +
      '#nexusAdvancedReport[hidden]{display:none!important}' +
      '#nexusAdvancedReportBody{margin:0;min-width:max-content;white-space:pre-wrap;overflow-wrap:anywhere;font:10px/1.42 ui-monospace,SFMono-Regular,Consolas,monospace;color:#293c4b}' +
      '@media(max-width:720px){#nexusAdvancedReport{max-height:min(32vh,250px)}#nexusReportToggle{font-size:9px;padding:5px 7px}}';
    (document.head||document.documentElement).appendChild(style);
  }

  function installUi(){
    const monitor=document.getElementById('nexusExchangeMonitor');
    if(!monitor) return false;
    if(document.getElementById('nexusReportToggle')) return true;
    installCss();
    monitor.classList.add('nxmon-u011-report-host');

    const button=document.createElement('button');
    button.id='nexusReportToggle';
    button.type='button';
    button.textContent='Rapport';
    button.setAttribute('aria-controls','nexusAdvancedReport');
    button.setAttribute('aria-expanded','false');

    const panel=document.createElement('div');
    panel.id='nexusAdvancedReport';
    panel.hidden=true;
    panel.setAttribute('role','region');
    panel.setAttribute('aria-label','Rapport technique NEXUS');
    panel.innerHTML='<pre id="nexusAdvancedReportBody"></pre>';

    button.addEventListener('click',()=>{
      const opening=panel.hidden;
      panel.hidden=!opening;
      button.textContent=opening?'Rapport ▲':'Rapport';
      button.setAttribute('aria-expanded',String(opening));
      if(opening){
        panel.scrollTop=panel.scrollHeight;
        append('REPORT','OPEN');
      } else {
        append('REPORT','CLOSE');
      }
    });

    monitor.appendChild(button);
    monitor.appendChild(panel);
    append('BOOT','report_panel_ready=true;scrollable=true;hidden_by_default=true;v009_arch005_frozen=true');
    return true;
  }

  function observe(){
    window.addEventListener('message',ev=>{
      if(ev.source!==window || !ev.data || typeof ev.data!=='object') return;
      const channel=clip(ev.data.channel,120);
      if(channel && !CHANNELS.has(channel) && !/^NEXUS_/.test(channel)) return;
      const type=clip(ev.data.type||'MESSAGE',120);
      let detail='';
      try{ detail=JSON.stringify(ev.data); }catch(_){ detail=String(ev.data); }
      append(type,detail);
    },true);

    for(const name of [
      'nexus:compare-llm-request',
      'nexus:compare-llm-receipt',
      'nexus:compare-llm-failed'
    ]){
      window.addEventListener(name,ev=>{
        let detail='';
        try{ detail=JSON.stringify(ev.detail||{}); }catch(_){ detail=String(ev.detail||''); }
        append(name,detail);
      });
    }
  }

  function boot(){
    if(installUi()) return;
    let tries=0;
    const timer=setInterval(()=>{
      tries++;
      if(installUi() || tries>100) clearInterval(timer);
    },100);
  }

  observe();
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();

  window.NexusAdvancedReport={
    append,
    open(){
      const b=document.getElementById('nexusReportToggle');
      if(b && b.getAttribute('aria-expanded')!=='true') b.click();
    },
    close(){
      const b=document.getElementById('nexusReportToggle');
      if(b && b.getAttribute('aria-expanded')==='true') b.click();
    }
  };
})();
