from pathlib import Path
import re, sys

root = Path(sys.argv[1]).resolve()
assets = root / 'app/src/main/assets/nexus'
chat = assets / 'chatgpt_provider_c002.js'
zai = assets / 'zai_provider_c002.js'
gradle = root / 'app/build.gradle.kts'
lock = root / 'RECONCILIATION_LOCK.txt'

c = chat.read_text()
old = "      const auth=detectAuth();\n      if(auth.state!=='AUTHENTICATED') throw new Error('CHATGPT_NOT_AUTHENTICATED:'+auth.state);\n"
new = "      const observedAuth=detectAuth();\n      const userConfirmed=(envelope.user_confirmed_connected===true);\n      const auth=userConfirmed\n        ? {...observedAuth,state:'AUTHENTICATED',reason:'USER_CONFIRMED_CONNECTED__'+String(observedAuth.state||'UNKNOWN')}\n        : observedAuth;\n      if(auth.state!=='AUTHENTICATED') throw new Error('CHATGPT_NOT_AUTHENTICATED:'+auth.state);\n"
assert old in c, 'ChatGPT auth gate anchor missing'
chat.write_text(c.replace(old,new,1))

z = zai.read_text()
z = z.replace('function parseCompleteResultCandidate(text,envelope){','function parseCompleteResultCandidate(text){',1)
corr = " if(envelope){ if(envelope.context_pack_id&&parsed.pack_id!==envelope.context_pack_id) continue; if(envelope.comparison_id&&parsed.comparison_id!==envelope.comparison_id) continue; }"
assert corr in z, 'Z.ai correlation prefilter anchor missing'
z = z.replace(corr,'',1)

start = z.index("  async function waitForModelResult(bridgeRunId,beforeSnapshot,envelope,timeout=180000){")
end = z.index("  async function executeJob", start)
m_start, m_end = start, end
golden_wait = """  async function waitForModelResult(bridgeRunId,beforeCount,timeout=160000){
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
        if(candidate.normalized_text===validText){
          if(!validSince) validSince=Date.now();
        }else{
          validText=candidate.normalized_text;
          validParsed=candidate.parsed;
          validSince=Date.now();
          await progress(bridgeRunId,'ZAI_JSON_COMPLETE_DETECTED');
        }
        if(Date.now()-validSince>=5000){
          return {text:validText,parsed:validParsed,node_count:nodes.length,json_stable_ms:Date.now()-validSince};
        }
        break;
      }
      await new Promise(r=>setTimeout(r,400));
    }
    throw new Error('ZAI_RESPONSE_TIMEOUT_BEFORE_STABLE_COMPLETE_JSON__response_nodes='+String(lastCount));
  }
  async function executeJob"""
z = z[:m_start] + golden_wait + z[m_end:]

old = "      const beforeCount=responseNodes().length; const beforeSnapshot=responseSnapshot(); const prompt=buildPrompt(envelope); setComposerText(composer,prompt); const send=await waitForSendReady(composer);"
new = "      const beforeCount=responseNodes().length; const prompt=buildPrompt(envelope); setComposerText(composer,prompt); const send=await waitForSendReady(composer);"
assert old in z, 'Z.ai pre-send snapshot anchor missing'
z = z.replace(old,new,1)
old = "      const result=await waitForModelResult(bridgeRunId,beforeSnapshot,envelope); await progress(bridgeRunId,'ZAI_UI_RESPONSE_CAPTURED');"
new = "      const result=await waitForModelResult(bridgeRunId,beforeCount); await progress(bridgeRunId,'ZAI_UI_RESPONSE_CAPTURED');"
assert old in z, 'Z.ai result call anchor missing'
z = z.replace(old,new,1)
old = 'response_count:result.node_count,changed_response_count:result.changed_node_count||null,json_stable_ms:result.json_stable_ms||null'
new = 'response_count:result.node_count,json_stable_ms:result.json_stable_ms||null'
assert old in z, 'Z.ai provider meta anchor missing'
z = z.replace(old,new,1)
zai.write_text(z)

g = gradle.read_text()
assert 'versionCode = 75' in g
assert 'versionName = "0.0.75-v007-golden-recovery003-auth-exec-fix"' in g
g = g.replace('versionCode = 75','versionCode = 76',1)
g = g.replace('versionName = "0.0.75-v007-golden-recovery003-auth-exec-fix"','versionName = "0.0.76-v007-golden-recovery004-golden-diff-fix"',1)
gradle.write_text(g)

lock.write_text(lock.read_text() +
    'GOLDEN_RECOVERY004_CHATGPT_AUTH=USER_CONFIRMED_CONNECTED_CONSUMED_AFTER_NATIVE_ORIGIN_GUARD\\n'
    'GOLDEN_RECOVERY004_CHATGPT_AUTO_LOGIN=NOT_ADDED\\n'
    'GOLDEN_RECOVERY004_ZAI_CAPTURE=RESTORED_DEVICE_PASS_COUNT_BASED_JSON_STABILITY\\n'
    'GOLDEN_RECOVERY004_ZAI_M024_PROMPT_POLICY=PRESERVED\\n'
    'GOLDEN_RECOVERY004_GEMINI=UNCHANGED_FROM_RECOVERY003_DEVICE_PASS_OBSERVED\\n'
    'GOLDEN_RECOVERY004_DEVICE_PASS=NOT_YET_ACQUIRED\\n')

cc=chat.read_text(); zz=zai.read_text()
assert 'user_confirmed_connected===true' in cc
assert 'CHATGPT_NOT_AUTHENTICATED' in cc
assert 'function parseCompleteResultCandidate(text){' in zz
assert 'waitForModelResult(bridgeRunId,beforeCount,timeout=160000)' in zz
assert 'const start=Math.min(beforeCount,nodes.length);' in zz
assert 'Date.now()-validSince>=5000' in zz
assert 'parseCompleteResultCandidate(txt);' in zz
assert 'parseCompleteResultCandidate(txt,envelope)' not in zz
assert 'changed_response_count' not in zz
assert 'Research policy OPTIONAL' in zz
