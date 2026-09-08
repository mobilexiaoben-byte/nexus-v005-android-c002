from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Rebuild strictly from Claude010, which itself is derived from the validated UIRETRY1 baseline.
subprocess.run(
    ["python3", str(repo / "executionproof010_claude" / "derive.py"), str(repo), str(work)],
    check=True,
)

# Side-by-side diagnostic identity.
p = work / "app/build.gradle.kts"
g = p.read_text()
for before, after in [
    ('applicationId = "nexus.android.c002.claudeexecutionproof010"', 'applicationId = "nexus.android.c002.claudeauthdiagnostic011"'),
    ('versionCode = 11', 'versionCode = 12'),
    ('versionName = "0.0.11-c002-claude-executionproof010"', 'versionName = "0.0.12-c002-claude-authdiag011"'),
]:
    assert g.count(before) == 1, f"gradle anchor mismatch: {before}"
    g = g.replace(before, after)
p.write_text(g)

p = work / "app/src/main/AndroidManifest.xml"
m = p.read_text()
old_label = 'android:label="NEXUS C002 CLAUDE EXECUTION PROOF 010"'
assert m.count(old_label) == 1, "manifest label mismatch"
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE AUTH DIAGNOSTIC 011"'))

main = work / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main.read_text()

for before, after in [
    ('nexus_provider_profile_c002_claude_executionproof010', 'nexus_provider_profile_c002_claude_authdiag011'),
    ('private var lastAuthState: String? = null\n', 'private var lastAuthState: String? = null\n    private var lastAuthDiagnosticFingerprint: String? = null\n'),
    ('                    lastAuthState = null\n', '                    lastAuthState = null\n                    lastAuthDiagnosticFingerprint = null\n'),
]:
    assert s.count(before) == 1, f"main anchor mismatch: {before}"
    s = s.replace(before, after)

old_handle = '''    private fun handleStatus(origin: String, message: JSONObject) {
        if (executionStarted || describePassed) return
        val auth = message.optJSONObject("status") ?: run {
            block("ANDROID_DESCRIBE_STATUS_MISSING")
            return
        }
        val authState = auth.optString("state", "UNKNOWN")
        val authChanged = authState != lastAuthState
        if (authChanged) {
            lastAuthState = authState
            recordDiagnostic("bridgeStatus", origin, "auth_state=$authState")
        }

        val descriptor = BridgeDescriptor(
            authenticated = authState == "AUTHENTICATED",
            origin = origin,
            targetCount = 1,
            adapterReady = true,
            missingFeatures = emptySet()
        )
        val gate = RuntimeGate.validateDescriptor(descriptor, CLAUDE_ORIGIN)
        if (!gate.pass) {
            if (gate.code == "ANDROID_AUTH_REQUIRED") {
                if (authChanged || currentHeadline != AUTH_REQUIRED_HEADLINE) {
                    currentHeadline = AUTH_REQUIRED_HEADLINE
                    currentBody = null
                    renderStatus()
                }
            } else {
                block("DESCRIBE_${gate.code}")
            }
            return
        }

        describePassed = true
        recordDiagnostic("DESCRIBE_PASS", origin, "authenticated=true")
        currentHeadline = "DESCRIBE PASS — execution proof starting"
        currentBody = null
        renderStatus()
        startExecutionProof(origin)
    }
'''
new_handle = '''    private fun handleStatus(origin: String, message: JSONObject) {
        if (proofStopped) return
        val auth = message.optJSONObject("status") ?: run {
            block("ANDROID_DIAGNOSTIC_STATUS_MISSING")
            return
        }
        val authState = auth.optString("state", "UNKNOWN")
        val reason = auth.optString("reason", "NO_REASON")
        val diagnostic = auth.optJSONObject("diagnostic") ?: JSONObject()
        val readyState = diagnostic.optString("ready_state", "?")
        val bodyPresent = diagnostic.optBoolean("body_present", false)
        val bodyChildren = diagnostic.optInt("body_child_count", -1)
        val bodyTextLength = diagnostic.optInt("body_text_length", -1)
        val inputCount = diagnostic.optInt("visible_input_count", -1)
        val buttonCount = diagnostic.optInt("visible_button_count", -1)
        val authCandidateCount = diagnostic.optJSONArray("visible_auth_candidates")?.length() ?: -1
        val tokenHits = diagnostic.optJSONArray("auth_token_hits")?.let { arr ->
            (0 until arr.length()).mapNotNull { i -> arr.optString(i).takeIf { it.isNotBlank() } }.joinToString(",")
        }.orEmpty()

        val fingerprint = listOf(
            authState, reason, readyState, bodyPresent.toString(), bodyChildren.toString(),
            bodyTextLength.toString(), inputCount.toString(), buttonCount.toString(),
            authCandidateCount.toString(), tokenHits
        ).joinToString("|")
        if (fingerprint != lastAuthDiagnosticFingerprint) {
            lastAuthDiagnosticFingerprint = fingerprint
            lastAuthState = authState
            recordDiagnostic(
                "CLAUDE_AUTH_SNAPSHOT",
                origin,
                "state=$authState;reason=${sanitizeCode(reason)};ready=$readyState;body=$bodyPresent;children=$bodyChildren;text_len=$bodyTextLength;inputs=$inputCount;buttons=$buttonCount;auth_candidates=$authCandidateCount;tokens=${sanitizeCode(tokenHits)}"
            )
        }

        currentHeadline = when (authState) {
            "AUTHENTICATED" -> "AUTH SIGNAL DETECTED — DESCRIBE WOULD PASS — NO JOB DISPATCHED"
            "UNAUTHENTICATED" -> "UNAUTH SIGNAL DETECTED — NO JOB DISPATCHED"
            else -> "AUTH DIAGNOSTIC 011 — UNKNOWN — NO JOB DISPATCHED"
        }
        currentBody = diagnostic.toString(2).take(MAX_DIAGNOSTIC_BODY_CHARS)
        renderStatus()
    }
'''
assert s.count(old_handle) == 1, "handleStatus anchor mismatch"
s = s.replace(old_handle, new_handle)

# Diagnostic build must never dispatch a provider job. Keep the old proof function as dead code
# so the derivative is small, but prove there is no call site from handleStatus.
for before, after in [
    ('const val BRIDGE_RUN_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-BRIDGE-001"', 'const val BRIDGE_RUN_ID = "V005-C002-CLAUDE-AUTH-DIAGNOSTIC-011-BRIDGE-001"'),
    ('const val ACTIVE_HEADLINE = "CLAUDE EXECUTION PROOF 010 — authenticate in Claude; one read-only proof job will run after DESCRIBE PASS"', 'const val ACTIVE_HEADLINE = "CLAUDE AUTH DIAGNOSTIC 011 — NO JOB DISPATCHED — inspect auth/UI signals only"'),
    ('const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; execution starts only after authenticated DESCRIBE PASS"', 'const val AUTH_REQUIRED_HEADLINE = "AUTH DIAGNOSTIC 011 — NO JOB DISPATCHED"'),
    ('const val EXPANDED_STATUS_LINES = 10', 'const val EXPANDED_STATUS_LINES = 18\n        const val MAX_DIAGNOSTIC_BODY_CHARS = 6000'),
]:
    assert s.count(before) == 1, f"constant anchor mismatch: {before}"
    s = s.replace(before, after)

assert 'startExecutionProof(origin)' not in new_handle
main.write_text(s)

provider = work / "app/src/main/assets/nexus/claude_provider_c002.js"
j = provider.read_text()

anchor = '''  function authActionTexts(){
    const accepted=new Set([
      'log in','login','sign in','sign up','signup',
      'se connecter','connexion',"s'inscrire",'s’inscrire','inscription'
    ]);
    const out=[];
    for(const el of [...document.querySelectorAll('button,a')].filter(visible)){
      const t=String(el.innerText||el.textContent||'').replace(/\\s+/g,' ').trim().toLowerCase();
      if(accepted.has(t)) out.push(t);
    }
    return [...new Set(out)].sort();
  }
'''
insert = anchor + '''
  function safeAttr(el,name){
    const v=String(el?.getAttribute?.(name)||'').replace(/\\s+/g,' ').trim();
    return v.slice(0,120);
  }

  function describeElement(el){
    return {
      tag:String(el?.tagName||'').toLowerCase(),
      role:safeAttr(el,'role'),
      type:safeAttr(el,'type'),
      aria_label:safeAttr(el,'aria-label'),
      placeholder:safeAttr(el,'placeholder'),
      data_testid:safeAttr(el,'data-testid'),
      contenteditable:safeAttr(el,'contenteditable')
    };
  }

  function authCandidateElements(){
    const re=/(log\\s*in|login|sign\\s*in|sign\\s*up|create\\s+account|get\\s+started|continue\\s+with|se\\s+connecter|connexion|inscri|email|google|apple)/i;
    const out=[];
    for(const el of [...document.querySelectorAll('button,a,[role="button"]')].filter(visible)){
      const text=String(el.innerText||el.textContent||'').replace(/\\s+/g,' ').trim().slice(0,100);
      const aria=safeAttr(el,'aria-label');
      const title=safeAttr(el,'title');
      const hay=[text,aria,title].join(' ');
      if(!re.test(hay)) continue;
      out.push({tag:String(el.tagName||'').toLowerCase(),text,aria_label:aria,title});
      if(out.length>=12) break;
    }
    return out;
  }

  function diagnosticSnapshot(){
    const inputSelectors='textarea,input,[contenteditable="true"],[role="textbox"]';
    const inputs=[...document.querySelectorAll(inputSelectors)].filter(visible).slice(0,12).map(describeElement);
    const buttons=[...document.querySelectorAll('button,a,[role="button"]')].filter(visible);
    const bodyText=String(document.body?.innerText||'').toLowerCase();
    const tokens=['log in','login','sign in','sign up','create account','get started','se connecter','connexion','inscription'];
    return {
      ready_state:document.readyState,
      body_present:!!document.body,
      body_child_count:document.body?.children?.length ?? -1,
      body_text_length:String(document.body?.innerText||'').length,
      visible_input_count:inputs.length,
      visible_inputs:inputs,
      visible_button_count:buttons.length,
      visible_auth_candidates:authCandidateElements(),
      auth_token_hits:tokens.filter(t=>bodyText.includes(t)),
      main_count:document.querySelectorAll('main').length,
      dialog_count:document.querySelectorAll('[role="dialog"]').length,
      pathname:location.pathname
    };
  }
'''
assert j.count(anchor) == 1, "authActionTexts anchor mismatch"
j = j.replace(anchor, insert)

old_return = '''    return {
      state,reason,
      observed_at:new Date().toISOString(),
      observed_at_ms:Date.now(),
      path:location.pathname,
      evidence:{
        positive,
        negative:neg.map(x=>'visible_auth_action:'+x),
        support
      }
    };
'''
new_return = '''    return {
      state,reason,
      observed_at:new Date().toISOString(),
      observed_at_ms:Date.now(),
      path:location.pathname,
      evidence:{
        positive,
        negative:neg.map(x=>'visible_auth_action:'+x),
        support
      },
      diagnostic:diagnosticSnapshot()
    };
'''
assert j.count(old_return) == 1, "detectAuth return anchor mismatch"
j = j.replace(old_return, new_return)

old_publish = '''  async function publishStatus(){
    const s=detectAuth();
    if(!running) show('AUTH: '+s.state+' — '+s.reason);
    try{ await nativeSend({channel:CHANNEL,type:'CLAUDE_STATUS',status:s}); }catch(_){
    }
  }
'''
new_publish = '''  async function publishStatus(){
    const s=detectAuth();
    if(!running){
      const d=s.diagnostic||{};
      show('AUTH: '+s.state+' — '+s.reason+' — ready='+String(d.ready_state)+' inputs='+String(d.visible_input_count)+' auth_candidates='+String((d.visible_auth_candidates||[]).length));
    }
    try{ await nativeSend({channel:CHANNEL,type:'CLAUDE_STATUS',status:s}); }catch(_){
    }
  }
'''
assert j.count(old_publish) == 1, "publishStatus anchor mismatch"
j = j.replace(old_publish, new_publish)

old_listener = '''  nativeOnMessage((msg,sender,sendResponse)=>{
    if(!msg || msg.channel!==CHANNEL || msg.type!=='EXECUTE_JOB') return;
    if(running){
      sendResponse({ok:false,error:'CLAUDE_PROVIDER_ALREADY_RUNNING'});
      return;
    }
    sendResponse({ok:true,accepted:true});
    setTimeout(()=>executeJob(msg.bridge_run_id,msg.envelope),0);
    return;
  });
'''
new_listener = '''  nativeOnMessage((msg,sender,sendResponse)=>{
    if(!msg || msg.channel!==CHANNEL || msg.type!=='EXECUTE_JOB') return;
    sendResponse({ok:false,error:'CLAUDE_AUTH_DIAGNOSTIC_011_NO_EXECUTION'});
    show('AUTH DIAGNOSTIC 011 — EXECUTE_JOB BLOCKED');
    return;
  });
'''
assert j.count(old_listener) == 1, "listener anchor mismatch"
j = j.replace(old_listener, new_listener)

assert 'setTimeout(()=>executeJob' not in j
assert 'CLAUDE_AUTH_DIAGNOSTIC_011_NO_EXECUTION' in j
assert 'diagnostic:diagnosticSnapshot()' in j
provider.write_text(j)
