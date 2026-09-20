from pathlib import Path
import re, sys

root=Path(sys.argv[1]).resolve()
assets=root/"app/src/main/assets/nexus"
main_path=root/"app/src/main/java/nexus/android/c002/MainActivity.kt"

# ---------------- Native watchdog ----------------
m=main_path.read_text()
field_anchor="    private var terminalReceived = false\n"
assert field_anchor in m
if "lastProviderActivityAtMs" not in m:
    m=m.replace(field_anchor,field_anchor+
        "    private var executionStartedAtMs = 0L\n"
        "    private var lastProviderActivityAtMs = 0L\n",1)

old="""        handler.postDelayed({
            if (!terminalReceived && !proofStopped) block("ANDROID_TERMINAL_TIMEOUT")
        }, TERMINAL_TIMEOUT_MS)
"""
new="""        executionStartedAtMs = android.os.SystemClock.elapsedRealtime()
        lastProviderActivityAtMs = executionStartedAtMs
        scheduleTerminalWatchdog()
"""
assert old in m
m=m.replace(old,new,1)

helper_anchor="    private fun postExecutionWhenBridgeReady(origin: String, json: String, attempt: Int) {\n"
assert helper_anchor in m
if "private fun scheduleTerminalWatchdog()" not in m:
    helper="""    private fun markProviderActivity() {
        lastProviderActivityAtMs = android.os.SystemClock.elapsedRealtime()
    }

    private fun scheduleTerminalWatchdog() {
        handler.postDelayed({
            if (terminalReceived || proofStopped || !executionStarted) return@postDelayed
            val now = android.os.SystemClock.elapsedRealtime()
            val elapsed = now - executionStartedAtMs
            val idle = now - lastProviderActivityAtMs
            val required = proofJob?.researchPolicy == nexus.android.c002.core.ResearchPolicy.REQUIRED
            val hardLimit = if (required) 900_000L else 420_000L
            val idleLimit = if (required) 240_000L else 120_000L
            when {
                elapsed >= hardLimit -> block("ANDROID_TERMINAL_HARD_TIMEOUT")
                ackPassed && idle >= idleLimit -> block("ANDROID_PROVIDER_INACTIVITY_TIMEOUT")
                else -> scheduleTerminalWatchdog()
            }
        }, 5_000L)
    }

"""
    m=m.replace(helper_anchor,helper+helper_anchor,1)

# Any accepted ACK / correlated progress is real activity.
m=m.replace("        ackPassed = true\n", "        ackPassed = true\n        markProviderActivity()\n",1)
m=m.replace('        val jobStatus = message.optString("job_status", "UNKNOWN").take(96)\n',
            '        val jobStatus = message.optString("job_status", "UNKNOWN").take(96)\n        markProviderActivity()\n',1)

# Terminal PASS only after correlation, provider ok, and Result Pack validation.
premature="""        terminalReceived = true
        monitorPass()
        finishReadableMonitorReport(true, "Result Pack validé et cycle terminé.")
"""
assert premature in m
m=m.replace(premature,"",1)
validation_anchor="""        if (packValidation != "PASS") {
            block(packValidation)
            return
        }

"""
assert validation_anchor in m
m=m.replace(validation_anchor,validation_anchor+
    '        terminalReceived = true\n'
    '        markProviderActivity()\n'
    '        monitorPass()\n'
    '        finishReadableMonitorReport(true, "Result Pack validé et cycle terminé.")\n\n',1)

# Fixed terminal timeout constant is no longer an execution authority.
m=m.replace("        const val TERMINAL_TIMEOUT_MS = 190_000L\n","",1)
main_path.write_text(m)

# ---------------- ChatGPT provider watchdog ----------------
chat=assets/"chatgpt_provider_c002.js"
c=chat.read_text()
assert "async function waitForAssistantResult" in c
if "function providerResultBudgetMs(envelope)" not in c:
    anchor="  async function waitForAssistantResult"
    helper="""  function providerResultBudgetMs(envelope){
    return String(envelope?.research_policy||'OPTIONAL')==='REQUIRED' ? 600000 : 300000;
  }

  function chatgptGenerating(){
    const selectors=[
      'button[aria-label*="stop" i]',
      'button[aria-label*="arrêter" i]',
      'button[data-testid*="stop" i]'
    ];
    return selectors.some(s=>[...document.querySelectorAll(s)].some(visible));
  }

"""
    c=c.replace(anchor,helper+anchor,1)

# make wait deadline policy-driven at call sites, and emit activity.
c=c.replace("waitForAssistantResult(beforeSnapshot,envelope,80000)",
            "waitForAssistantResult(beforeSnapshot,envelope,providerResultBudgetMs(envelope))")
c=c.replace("waitForAssistantResult(beforeSnapshot,envelope,80000,graceUntil)",
            "waitForAssistantResult(beforeSnapshot,envelope,providerResultBudgetMs(envelope),graceUntil)")
old_decl="    let validText='',validSince=0,validParsed=null,lastNodeCount=beforeSnapshot.size,lastChangedCount=0;\n"
assert old_decl in c
if "lastActivityReportAt" not in c[c.index("async function waitForAssistantResult"):c.index("async function executeJob")]:
    c=c.replace(old_decl,old_decl+"    let lastObservedSignature='',lastActivityReportAt=0,responseStartedReported=false;\n",1)
loop_anchor="""      lastChangedCount=changed.length;
      for(let i=changed.length-1;i>=0;i--){
"""
assert loop_anchor in c
activity="""      lastChangedCount=changed.length;
      const newestText=changed.length ? assistantNodeText(changed[changed.length-1]) : '';
      const signature=newestText.slice(-1200);
      const generating=chatgptGenerating();
      const now=Date.now();
      if((signature && signature!==lastObservedSignature) || (generating && now-lastActivityReportAt>=10000)){
        if(signature) lastObservedSignature=signature;
        lastActivityReportAt=now;
        if(!responseStartedReported){
          responseStartedReported=true;
          await progress(bridgeRunId,'CHATGPT_UI_RESPONSE_STARTED');
        }else{
          await progress(bridgeRunId,'CHATGPT_UI_RESPONSE_ACTIVITY');
        }
      }
      for(let i=changed.length-1;i>=0;i--){
"""
# wait function needs bridgeRunId parameter
c=c.replace("async function waitForAssistantResult(beforeSnapshot, envelope, timeout=80000, errorGraceUntil=0)",
            "async function waitForAssistantResult(bridgeRunId, beforeSnapshot, envelope, timeout=80000, errorGraceUntil=0)",1)
c=c.replace("waitForAssistantResult(beforeSnapshot,envelope,providerResultBudgetMs(envelope))",
            "waitForAssistantResult(bridgeRunId,beforeSnapshot,envelope,providerResultBudgetMs(envelope))")
c=c.replace("waitForAssistantResult(beforeSnapshot,envelope,providerResultBudgetMs(envelope),graceUntil)",
            "waitForAssistantResult(bridgeRunId,beforeSnapshot,envelope,providerResultBudgetMs(envelope),graceUntil)")
assert loop_anchor in c
c=c.replace(loop_anchor,activity,1)
chat.write_text(c)

# ---------------- Gemini provider watchdog ----------------
gem=assets/"gemini_provider_c002.js"
g=gem.read_text()
assert "async function waitForModelResult" in g
if "function providerResultBudgetMs(envelope)" not in g:
    anchor="  async function waitForModelResult"
    g=g.replace(anchor,"""  function providerResultBudgetMs(envelope){
    return String(envelope?.research_policy||'OPTIONAL')==='REQUIRED' ? 600000 : 300000;
  }

"""+anchor,1)
# default calls become policy budget
g=g.replace("waitForModelResult(bridgeRunId,beforeSnapshot,envelope)",
            "waitForModelResult(bridgeRunId,beforeSnapshot,envelope,providerResultBudgetMs(envelope))",1)
old_decl="    let validText='',validSince=0,validParsed=null,lastCount=beforeSnapshot.size,lastChangedCount=0;\n"
assert old_decl in g
if "lastActivityReportAt" not in g[g.index("async function waitForModelResult"):g.index("async function executeJob")]:
    g=g.replace(old_decl,old_decl+"    let lastObservedSignature='',lastActivityReportAt=0,responseStartedReported=false;\n",1)
loop_anchor="""      lastChangedCount=changed.length;
      for(let i=changed.length-1;i>=0;i--){
"""
assert loop_anchor in g
activity="""      lastChangedCount=changed.length;
      const newestText=changed.length ? modelNodeText(changed[changed.length-1]) : '';
      const signature=newestText.slice(-1200);
      const active=generating();
      const now=Date.now();
      if((signature && signature!==lastObservedSignature) || (active && now-lastActivityReportAt>=10000)){
        if(signature) lastObservedSignature=signature;
        lastActivityReportAt=now;
        if(!responseStartedReported){
          responseStartedReported=true;
          await progress(bridgeRunId,'GEMINI_UI_RESPONSE_STARTED');
        }else{
          await progress(bridgeRunId,'GEMINI_UI_RESPONSE_ACTIVITY');
        }
      }
      for(let i=changed.length-1;i>=0;i--){
"""
g=g.replace(loop_anchor,activity,1)
gem.write_text(g)

# Fail-closed assertions.
m=main_path.read_text(); c=chat.read_text(); g=gem.read_text()
assert "ANDROID_TERMINAL_TIMEOUT" not in m
assert "ANDROID_PROVIDER_INACTIVITY_TIMEOUT" in m
assert "ANDROID_TERMINAL_HARD_TIMEOUT" in m
assert "scheduleTerminalWatchdog()" in m
assert m.index('val packValidation = validateResultPack') < m.index('terminalReceived = true')
assert "providerResultBudgetMs(envelope)" in c
assert "CHATGPT_UI_RESPONSE_ACTIVITY" in c
assert "providerResultBudgetMs(envelope)" in g
assert "GEMINI_UI_RESPONSE_ACTIVITY" in g
