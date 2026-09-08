from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Rebuild strictly from validated RESULT DOM DIAGNOSTIC 015.
subprocess.run([
    'python3', str(repo / 'clauderesultdomdiag015' / 'derive.py'), str(repo), str(work)
], check=True)

# Traceable APK identity only.
p = work / 'app/build.gradle.kts'
g = p.read_text()
for before, after in [
    ('applicationId = "nexus.android.c002.clauderesultdomdiag015"', 'applicationId = "nexus.android.c002.claudeprompthardening016"'),
    ('versionCode = 16', 'versionCode = 17'),
    ('versionName = "0.0.16-c002-claude-resultdomdiag015"', 'versionName = "0.0.17-c002-claude-prompthardening016"'),
]:
    assert g.count(before) == 1, f'gradle anchor mismatch: {before}'
    g = g.replace(before, after)
p.write_text(g)

p = work / 'app/src/main/AndroidManifest.xml'
m = p.read_text()
old_label = 'android:label="NEXUS C002 CLAUDE RESULT DOM DIAG 015"'
assert m.count(old_label) == 1, 'manifest label mismatch'
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE PROMPT HARDENING 016"'))

# Controller: align expected Result Pack contract with parser fingerprint gate and update proof identity.
main = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()
for before, after in [
    ('nexus_provider_profile_c002_claude_resultdomdiag015', 'nexus_provider_profile_c002_claude_promptsubmission016'),
    ('V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015-BRIDGE-001', 'V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016-BRIDGE-001'),
    ('V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015-001', 'V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016-001'),
    ('V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015-COMP-001', 'V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016-COMP-001'),
    ('V005_CLAUDE_RESULT_DOM_DIAGNOSTIC_015_V1', 'V005_CLAUDE_PROMPT_SUBMISSION_HARDENING_016_V1'),
    ('NEXUS_CLAUDE_RESULT_DOM_DIAGNOSTIC_015_OK', 'NEXUS_CLAUDE_PROMPT_SUBMISSION_HARDENING_016_OK'),
    ('this Android Claude result-DOM diagnostic proof', 'this Android Claude prompt-submission hardening proof'),
    ('.put("contract", "V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015")', '.put("contract", "V005-C002-CLAUDE-PROMPT-SUBMISSION-HARDENING-016")'),
]:
    assert before in s, f'identity anchor missing: {before}'
    s = s.replace(before, after)

audit_anchor = '''            .put("audit", JSONObject()\n                .put("external_research", false)\n'''
audit_repl = '''            .put("audit", JSONObject()\n                .put("analysis_fingerprint", job.frozenFingerprint)\n                .put("external_research", false)\n'''
assert s.count(audit_anchor) == 1, 'expected result audit anchor mismatch'
s = s.replace(audit_anchor, audit_repl)
main.write_text(s)

provider = work / 'app/src/main/assets/nexus/claude_provider_c002.js'
j = provider.read_text()

# Harden send-button selection: prefer an enabled button spatially associated with the live composer.
start = j.index('  function findSendButton(){\n')
end = j.index('\n  function isGenerating(){\n', start)
new_find = r'''  function findSendButton(){
    const composer=findComposer();
    const buttons=[...document.querySelectorAll('button')].filter(el=>visible(el)&&!el.disabled);
    if(composer){
      const cr=composer.getBoundingClientRect();
      const form=composer.closest('form');
      const nearby=[];
      for(const el of buttons){
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

    // Semantic fallback stays bounded to explicit send affordances; no global type=submit fallback.
    const selectors=[
      'button[aria-label*="Send" i]',
      'button[aria-label*="Envoyer" i]',
      'button[data-testid*="send" i]'
    ];
    for(const s of selectors){
      for(const el of document.querySelectorAll(s)){
        if(visible(el) && !el.disabled) return el;
      }
    }
    return null;
  }
'''
j = j[:start] + new_find + j[end:]

# Add bounded runtime confirmation. This does not inspect or modify response selectors.
anchor = '''  async function waitForStableJson(bridgeRunId,envelope,timeout=180000){\n'''
assert j.count(anchor) == 1, 'waitForStableJson anchor mismatch'
submit_helpers = r'''  function promptSubmissionSignal(envelope){
    const composer=findComposer();
    if(isGenerating()) return 'GENERATION_ACTIVE';
    if(!composer) return null;
    const text=composerText(composer).trim();
    const stillHasPack=text.includes(envelope.context_pack_id);
    const stillHasTail=text.includes('Generate the completed Result Pack now.');
    if(!stillHasPack && !stillHasTail && text.length<80) return 'COMPOSER_CLEARED';
    return null;
  }

  async function waitForPromptSubmission(envelope,timeout){
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      const signal=promptSubmissionSignal(envelope);
      if(signal) return signal;
      await new Promise(r=>setTimeout(r,200));
    }
    return null;
  }

'''
j = j.replace(anchor, submit_helpers + anchor)

old_send = '''      const send=await waitForSendReady(composer);\n\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');\n      send.click();\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT');\n\n      const result=await waitForStableJson(bridgeRunId,envelope);\n'''
new_send = '''      let send=await waitForSendReady(composer);\n\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');\n      send.focus();\n      send.click();\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_CLICK_1');\n      let submission=await waitForPromptSubmission(envelope,4000);\n\n      if(!submission){\n        await progress(bridgeRunId,'CLAUDE_UI_PROMPT_RETRY_1');\n        send=findSendButton();\n        if(!send) throw new Error('CLAUDE_SEND_BUTTON_NOT_READY_ON_RETRY');\n        send.focus();\n        send.click();\n        submission=await waitForPromptSubmission(envelope,6000);\n      }\n\n      if(!submission) throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED');\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED__'+submission);\n\n      const result=await waitForStableJson(bridgeRunId,envelope);\n'''
assert j.count(old_send) == 1, 'execute send block mismatch'
j = j.replace(old_send, new_send)

# Defense: old optimistic status must not survive.
assert "await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT');" not in j
assert 'CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED' in j
assert 'CLAUDE_UI_PROMPT_SENT_CONFIRMED__' in j
provider.write_text(j)
