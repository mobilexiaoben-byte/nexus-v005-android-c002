from pathlib import Path
import shutil
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
base = repo / 'base' / 'V005_ANDROID_CHROMIUM_WEBVIEW_C002'
if work.exists():
    shutil.rmtree(work)
shutil.copytree(base, work)

# Carry forward the validated EXECUTION-PROOF-006 native controller and ChatGPT adapter.
shutil.copy2(repo / 'executionproof006' / 'MainActivity.kt', work / 'app/src/main/java/nexus/android/c002/MainActivity.kt')
shutil.copy2(repo / 'executionproof006' / 'chatgpt_provider_c002.js', work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js')

# Side-by-side diagnostic package/profile.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.c002"', 'applicationId = "nexus.android.c002.executionproof006.uiretry1"')
s = s.replace('versionCode = 2', 'versionCode = 10')
s = s.replace('versionName = "0.0.2-c002"', 'versionName = "0.0.10-c002-executionproof006-uiretry1"')
p.write_text(s)

p = work / 'app/src/main/AndroidManifest.xml'
s = p.read_text()
old = 'android:label="NEXUS Android C002"'
assert s.count(old) == 1, 'manifest baseline mismatch'
p.write_text(s.replace(old, 'android:label="NEXUS C002 EXECUTION PROOF 006 UIRETRY1"'))

p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text()
needle = 'android:padding="12dp"\n        android:text="NEXUS C002 — initializing"'
repl = 'android:padding="8dp"\n        android:maxLines="2"\n        android:ellipsize="end"\n        android:clickable="true"\n        android:focusable="true"\n        android:text="EXECUTION PROOF 006 UIRETRY1 — initializing"'
assert s.count(needle) == 1, 'layout baseline mismatch'
p.write_text(s.replace(needle, repl))

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
old = 'nexus_provider_profile_c002_executionproof006'
assert s.count(old) == 1, 'profile source mismatch'
p.write_text(s.replace(old, 'nexus_provider_profile_c002_executionproof006_uiretry1'))

# Preserve the exact auth-host evidence chain: only these exact hosts are navigation additions.
p = work / 'app/src/main/java/nexus/android/c002/web/OriginPolicy.kt'
s = p.read_text()
needle = '            host == "anthropic.com" || host.endsWith(".anthropic.com")\n'
repl = '            host == "anthropic.com" || host.endsWith(".anthropic.com") ||\n            host == "accounts.google.com" ||\n            host == "accounts.youtube.com" ||\n            host == "accounts.google.fr"\n'
assert s.count(needle) == 1, 'policy baseline mismatch'
p.write_text(s.replace(needle, repl))

# Provider harness correction: detect the explicit ChatGPT UI failure, retry exactly once,
# keep the same correlated bridge_run_id/job, and fail closed after the bounded retry.
p = work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
s = p.read_text()
marker = '  function parseCompleteResultCandidate(text){\n'
helpers = r'''  function normalizeUiText(value){
    return String(value||'').replace(/\s+/g,' ').trim().toLowerCase();
  }

  function findRetryButton(){
    const accepted=new Set(['retry','try again','réessayer','reessayer']);
    for(const b of [...document.querySelectorAll('button')].filter(visible)){
      if(b.disabled) continue;
      const text=normalizeUiText(b.innerText||b.textContent||'');
      const aria=normalizeUiText(b.getAttribute('aria-label')||'');
      if(accepted.has(text) || accepted.has(aria)) return b;
    }
    return null;
  }

  function detectUiResponseError(){
    const retry=findRetryButton();
    if(retry) return {retry_available:true};
    const body=normalizeUiText(document.body?.innerText||'');
    const patterns=[
      'something went wrong',
      'une erreur s’est produite',
      "une erreur s'est produite",
      'un problème est survenu',
      'un probleme est survenu'
    ];
    if(patterns.some(p=>body.includes(p))) return {retry_available:false};
    return null;
  }

'''
assert s.count(marker) == 1, 'parse marker mismatch'
s = s.replace(marker, helpers + marker)

old_sig = '  async function waitForAssistantResult(beforeCount, timeout=160000){\n    const deadline=Date.now()+timeout;\n'
new_sig = '  async function waitForAssistantResult(beforeCount, timeout=80000, errorGraceUntil=0){\n    const deadline=Date.now()+timeout;\n'
assert s.count(old_sig) == 1, 'wait signature mismatch'
s = s.replace(old_sig, new_sig)

old_loop = '    while(Date.now()<deadline){\n      const nodes=assistantNodes();\n'
new_loop = '''    while(Date.now()<deadline){
      if(Date.now()>=errorGraceUntil){
        const uiError=detectUiResponseError();
        if(uiError){
          throw new Error(uiError.retry_available ? 'CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE' : 'CHATGPT_UI_RESPONSE_ERROR_NO_RETRY_CONTROL');
        }
      }
      const nodes=assistantNodes();
'''
assert s.count(old_loop) == 1, 'wait loop mismatch'
s = s.replace(old_loop, new_loop)

old_exec = '''      const result=await waitForAssistantResult(beforeCount);
      await progress(bridgeRunId,'CHATGPT_UI_RESPONSE_CAPTURED');
      const parsed=result.parsed || stripToJson(result.text);
'''
new_exec = '''      let retryCount=0;
      let result;
      try{
        result=await waitForAssistantResult(beforeCount,80000);
      }catch(firstErr){
        const firstCode=String(firstErr?.message||firstErr);
        if(firstCode!=='CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE') throw firstErr;
        await progress(bridgeRunId,'CHATGPT_UI_RESPONSE_ERROR_DETECTED');
        const retry=findRetryButton();
        if(!retry) throw new Error('CHATGPT_UI_RESPONSE_ERROR_RETRY_CONTROL_LOST');
        retry.click();
        retryCount=1;
        await progress(bridgeRunId,'CHATGPT_UI_RETRY_1_TRIGGERED');
        const graceUntil=Date.now()+5000;
        try{
          result=await waitForAssistantResult(beforeCount,80000,graceUntil);
        }catch(retryErr){
          const retryCode=String(retryErr?.message||retryErr);
          if(retryCode==='CHATGPT_UI_RESPONSE_ERROR_RETRY_AVAILABLE' || retryCode==='CHATGPT_UI_RESPONSE_ERROR_NO_RETRY_CONTROL'){
            throw new Error('CHATGPT_UI_RESPONSE_ERROR_AFTER_RETRY');
          }
          throw retryErr;
        }
      }
      await progress(bridgeRunId,'CHATGPT_UI_RESPONSE_CAPTURED');
      const parsed=result.parsed || stripToJson(result.text);
'''
assert s.count(old_exec) == 1, 'execute result wait mismatch'
s = s.replace(old_exec, new_exec)

old_meta = "          completion_rule:'COMPLETE_JSON_REQUIRED__STABLE_8000MS',\n          auth_observation:auth,\n"
new_meta = "          completion_rule:'COMPLETE_JSON_REQUIRED__STABLE_8000MS',\n          retry_count:retryCount,\n          retry_policy:'EXPLICIT_UI_ERROR_ONLY__MAX_1',\n          auth_observation:auth,\n"
assert s.count(old_meta) == 1, 'provider meta mismatch'
s = s.replace(old_meta, new_meta)

p.write_text(s)
