from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Rebuild strictly from OAUTH HANDOFF 014. OAuth/window policy, OriginPolicy,
# ChatGPT adapter and native bridge remain unchanged.
subprocess.run([
    'python3', str(repo / 'claudeoauthhandoff014' / 'derive.py'), str(repo), str(work)
], check=True)

# Traceable APK identity only.
p = work / 'app/build.gradle.kts'
g = p.read_text()
for before, after in [
    ('applicationId = "nexus.android.c002.claudeoauthhandoff014"', 'applicationId = "nexus.android.c002.clauderesultdomdiag015"'),
    ('versionCode = 15', 'versionCode = 16'),
    ('versionName = "0.0.15-c002-claude-oauthhandoff014"', 'versionName = "0.0.16-c002-claude-resultdomdiag015"'),
]:
    assert g.count(before) == 1, f'gradle anchor mismatch: {before}'
    g = g.replace(before, after)
p.write_text(g)

p = work / 'app/src/main/AndroidManifest.xml'
m = p.read_text()
old_label = 'android:label="NEXUS C002 CLAUDE OAUTH HANDOFF 014"'
assert m.count(old_label) == 1, 'manifest label mismatch'
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE RESULT DOM DIAG 015"'))

# Keep the same controller behavior, changing only proof identity for traceability.
main = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()
for before, after in [
    ('nexus_provider_profile_c002_claude_oauthhandoff014', 'nexus_provider_profile_c002_claude_resultdomdiag015'),
    ('V005-C002-CLAUDE-OAUTH-HANDOFF-014-BRIDGE-001', 'V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015-BRIDGE-001'),
    ('V005-C002-CLAUDE-OAUTH-HANDOFF-014-001', 'V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015-001'),
    ('V005-C002-CLAUDE-OAUTH-HANDOFF-014-COMP-001', 'V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015-COMP-001'),
    ('V005_CLAUDE_OAUTH_HANDOFF_014_V1', 'V005_CLAUDE_RESULT_DOM_DIAGNOSTIC_015_V1'),
    ('NEXUS_CLAUDE_OAUTH_HANDOFF_014_OK', 'NEXUS_CLAUDE_RESULT_DOM_DIAGNOSTIC_015_OK'),
    ('this Android Claude OAuth-handoff transport proof', 'this Android Claude result-DOM diagnostic proof'),
    ('.put("contract", "V005-C002-CLAUDE-OAUTH-HANDOFF-014")', '.put("contract", "V005-C002-CLAUDE-RESULT-DOM-DIAGNOSTIC-015")'),
]:
    assert before in s, f'identity anchor missing: {before}'
    s = s.replace(before, after)
main.write_text(s)

provider = work / 'app/src/main/assets/nexus/claude_provider_c002.js'
j = provider.read_text()

# Add a diagnostic-only scanner. It mirrors each rejection stage but DOES NOT
# alter findResultCandidates() or parseCandidate(). No selector is added.
anchor = '''  function findResultCandidates(envelope){\n'''
assert j.count(anchor) == 1, 'findResultCandidates anchor mismatch'
diag = r'''  function diagnoseResultDom(envelope){
    const selectors=[
      '[data-testid*="message" i]',
      '[data-testid*="assistant" i]',
      '[data-is-streaming]',
      '.prose',
      'article',
      'main div'
    ];
    const seen=new Set();
    const d={n:0,v:0,l:0,p:0,f:0,j:0,r:0,pm:0,cm:0,fm:0,pr:0,ok:0,cfp:0,mx:0};
    const expected=envelope.frozen_package?.output_contract?.expected_result_pack;
    if(expected?.audit?.analysis_fingerprint===envelope.frozen_fingerprint) d.cfp=1;

    for(const sel of selectors){
      for(const el of document.querySelectorAll(sel)){
        if(seen.has(el)) continue;
        seen.add(el); d.n++;
        if(!visible(el)) continue;
        d.v++;
        const text=String(el.innerText||el.textContent||'').trim();
        d.mx=Math.max(d.mx,text.length);
        if(text.length<100 || text.length>50000) continue;
        d.l++;
        if(text.includes(envelope.context_pack_id)) d.p++;
        if(text.includes(envelope.frozen_fingerprint)) d.f++;

        const raw=text;
        const variants=[raw];
        if(raw.startsWith('```')) variants.push(raw.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim());
        const a=raw.indexOf('{'), b=raw.lastIndexOf('}');
        if(a>=0 && b>a) variants.push(raw.slice(a,b+1));
        let nodeJson=false,nodeReq=false,nodePm=false,nodeCm=false,nodeFm=false,nodePr=false,nodeOk=false;
        for(const candidate of variants){
          try{
            const parsed=JSON.parse(candidate);
            if(!parsed || typeof parsed!=='object' || Array.isArray(parsed)) continue;
            nodeJson=true;
            const required=['result_pack_version','pack_id','comparison_id','model','answer','audit'];
            if(!required.every(k=>Object.prototype.hasOwnProperty.call(parsed,k))) continue;
            nodeReq=true;
            if(parsed.pack_id!==envelope.context_pack_id) continue;
            nodePm=true;
            if(parsed.comparison_id!==envelope.frozen_package?.comparison_id) continue;
            nodeCm=true;
            if(parsed.audit?.analysis_fingerprint!==envelope.frozen_fingerprint) continue;
            nodeFm=true;
            if(String(parsed.model?.provider||'').toUpperCase()!=='ANTHROPIC') continue;
            nodePr=true; nodeOk=true;
          }catch(_){ }
        }
        if(nodeJson) d.j++;
        if(nodeReq) d.r++;
        if(nodePm) d.pm++;
        if(nodeCm) d.cm++;
        if(nodeFm) d.fm++;
        if(nodePr) d.pr++;
        if(nodeOk) d.ok++;
      }
    }
    return d;
  }

  function compactDomDiag(d){
    return [
      'D015','n'+d.n,'v'+d.v,'l'+d.l,'p'+d.p,'f'+d.f,
      'j'+d.j,'r'+d.r,'pm'+d.pm,'cm'+d.cm,'fm'+d.fm,
      'pr'+d.pr,'ok'+d.ok,'cfp'+d.cfp,'mx'+d.mx
    ].join('_');
  }

'''
j = j.replace(anchor, diag + anchor)

# Pass bridgeRunId so diagnostics can be emitted as correlated PROVIDER_PROGRESS.
old_sig = '  async function waitForStableJson(envelope,timeout=180000){\n'
new_sig = '  async function waitForStableJson(bridgeRunId,envelope,timeout=180000){\n'
assert j.count(old_sig) == 1, 'waitForStableJson signature mismatch'
j = j.replace(old_sig, new_sig)

old_state = "    let validText='',validSince=0,validParsed=null,lastCandidateCount=0;\n"
new_state = "    let validText='',validSince=0,validParsed=null,lastCandidateCount=0,lastDiag='',lastDiagAt=0,latestDiag=null;\n"
assert j.count(old_state) == 1, 'wait state anchor mismatch'
j = j.replace(old_state, new_state)

loop_anchor = '''    while(Date.now()<deadline){\n      const candidates=findResultCandidates(envelope);\n'''
loop_repl = '''    while(Date.now()<deadline){
      latestDiag=diagnoseResultDom(envelope);
      const diagText=compactDomDiag(latestDiag);
      if(diagText!==lastDiag || Date.now()-lastDiagAt>=5000){
        lastDiag=diagText; lastDiagAt=Date.now();
        await progress(bridgeRunId,diagText);
      }
      const candidates=findResultCandidates(envelope);
'''
assert j.count(loop_anchor) == 1, 'loop anchor mismatch'
j = j.replace(loop_anchor, loop_repl)

old_timeout = "    throw new Error('CLAUDE_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__candidates='+String(lastCandidateCount));\n"
new_timeout = "    throw new Error('CLAUDE_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__'+compactDomDiag(latestDiag||{n:0,v:0,l:0,p:0,f:0,j:0,r:0,pm:0,cm:0,fm:0,pr:0,ok:0,cfp:0,mx:0}));\n"
assert j.count(old_timeout) == 1, 'timeout anchor mismatch'
j = j.replace(old_timeout, new_timeout)

old_call = '      const result=await waitForStableJson(envelope);\n'
new_call = '      const result=await waitForStableJson(bridgeRunId,envelope);\n'
assert j.count(old_call) == 1, 'wait call mismatch'
j = j.replace(old_call, new_call)

provider.write_text(j)
