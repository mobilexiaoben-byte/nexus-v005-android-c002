from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
subprocess.run(['python3', str(repo/'claudeprompthardening016'/'derive.py'), str(repo), str(work)], check=True)

# Branding is part of the derived Android source from 017 onward, not a one-off
# workflow patch. Any later derivative that rebuilds through 017 inherits it.
subprocess.run(['python3', str(repo/'branding'/'ensure_launcher.py'), str(work)], check=True)

p=work/'app/build.gradle.kts'; g=p.read_text()
for before,after in [
('applicationId = "nexus.android.c002.claudeprompthardening016"','applicationId = "nexus.android.c002.claudeturngeneration017"'),
('versionCode = 17','versionCode = 18'),
('versionName = "0.0.17-c002-claude-prompthardening016"','versionName = "0.0.18-c002-claude-turngeneration017"')]:
    assert g.count(before)==1, before; g=g.replace(before,after)
p.write_text(g)

p=work/'app/src/main/AndroidManifest.xml'; m=p.read_text(); old='android:label="NEXUS C002 CLAUDE PROMPT HARDENING 016"'; assert m.count(old)==1; p.write_text(m.replace(old,'android:label="NEXUS C002 CLAUDE TURN GENERATION DIAG 017"'))

main=work/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=main.read_text()
for before,after in [
('nexus_provider_profile_c002_claude_promptsubmission016','nexus_provider_profile_c002_claude_turngeneration017'),
('V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016-BRIDGE-001','V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017-BRIDGE-001'),
('V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016-001','V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017-001'),
('V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016-COMP-001','V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017-COMP-001'),
('V005_CLAUDE_PROMPT_SUBMISSION_HARDENING_016_V1','V005_CLAUDE_TURN_GENERATION_DIAGNOSTIC_017_V1'),
('NEXUS_CLAUDE_PROMPT_SUBMISSION_HARDENING_016_OK','NEXUS_CLAUDE_TURN_GENERATION_DIAGNOSTIC_017_OK'),
('this Android Claude prompt-submission hardening proof','this Android Claude turn-generation diagnostic proof'),
('.put("contract", "V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016")','.put("contract", "V005-C002-CLAUDE-TURN-GENERATION-DIAGNOSTIC-017")')]:
    assert before in s, before; s=s.replace(before,after)
main.write_text(s)

provider=work/'app/src/main/assets/nexus/claude_provider_c002.js'; j=provider.read_text()
anchor='  async function waitForStableJson(bridgeRunId,envelope,timeout=180000){\n'; assert j.count(anchor)==1
helpers=r'''  function turnGenerationSnapshot(envelope){
    const composer=findComposer();
    const d={c:composer?1:0,cp:0,po:0,u:0,a:0,s:0,st:0,g:isGenerating()?1:0};
    if(composer && composerText(composer).includes(envelope.context_pack_id)) d.cp=1;
    const outside=(el)=>!composer || (el!==composer && !composer.contains(el) && !el.contains(composer));
    const seen=new Set();
    for(const sel of ['[data-testid*="message" i]','article','.prose','main div']){
      for(const el of document.querySelectorAll(sel)){
        if(seen.has(el)||!visible(el)||!outside(el)) continue; seen.add(el);
        const text=String(el.innerText||el.textContent||'');
        if(text.includes(envelope.context_pack_id)) d.po++;
      }
    }
    for(const el of document.querySelectorAll('[data-testid*="user" i],[data-message-author-role="user"],[data-role="user"]')) if(visible(el)&&outside(el)) d.u++;
    for(const el of document.querySelectorAll('[data-testid*="assistant" i],[data-message-author-role="assistant"],[data-role="assistant"]')) if(visible(el)&&outside(el)) d.a++;
    for(const el of document.querySelectorAll('[data-is-streaming]')) if(visible(el)&&outside(el)) d.s++;
    for(const el of document.querySelectorAll('button')){
      if(!visible(el)) continue;
      const label=[el.getAttribute('aria-label'),el.getAttribute('title'),el.innerText].filter(Boolean).join(' ');
      if(/stop|arr[eê]ter|interrompre/i.test(label)) d.st++;
    }
    return d;
  }

  function compactTurnDiag(d){ return ['D017','c'+d.c,'cp'+d.cp,'po'+d.po,'u'+d.u,'a'+d.a,'s'+d.s,'st'+d.st,'g'+d.g].join('_'); }

  async function waitForTurnAndGeneration(bridgeRunId,envelope,baseline,timeout=30000){
    const deadline=Date.now()+timeout; let last='',lastAt=0,latest=baseline,userTurn=false;
    while(Date.now()<deadline){
      latest=turnGenerationSnapshot(envelope);
      if(latest.po>baseline.po || latest.u>baseline.u) userTurn=true;
      const generation=(latest.g===1 || latest.s>baseline.s || latest.st>baseline.st || latest.a>baseline.a);
      const text=compactTurnDiag(latest);
      if(text!==last || Date.now()-lastAt>=2000){ last=text; lastAt=Date.now(); await progress(bridgeRunId,text); }
      if(userTurn && generation){ await progress(bridgeRunId,'CLAUDE_GENERATION_OBSERVED__'+text); return latest; }
      await new Promise(r=>setTimeout(r,250));
    }
    const text=compactTurnDiag(latest);
    if(!userTurn) throw new Error('CLAUDE_USER_TURN_NOT_MATERIALIZED_AFTER_SUBMISSION__'+text);
    throw new Error('CLAUDE_GENERATION_NOT_OBSERVED_AFTER_SUBMISSION__'+text);
  }

'''
j=j.replace(anchor,helpers+anchor)
old="      let send=await waitForSendReady(composer);\n\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');\n"
new="      const turnBaseline=turnGenerationSnapshot(envelope);\n      await progress(bridgeRunId,'CLAUDE_TURN_BASELINE__'+compactTurnDiag(turnBaseline));\n      let send=await waitForSendReady(composer);\n\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');\n"
assert j.count(old)==1; j=j.replace(old,new)
old2="      if(!submission) throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED');\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED__'+submission);\n\n      const result=await waitForStableJson(bridgeRunId,envelope);\n"
new2="      if(!submission) throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED');\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED__'+submission);\n      await waitForTurnAndGeneration(bridgeRunId,envelope,turnBaseline);\n\n      const result=await waitForStableJson(bridgeRunId,envelope);\n"
assert j.count(old2)==1; j=j.replace(old2,new2)
provider.write_text(j)
