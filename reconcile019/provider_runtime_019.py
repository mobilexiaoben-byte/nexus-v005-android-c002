from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

exec((repo / "reconcile018" / "provider_runtime_018.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile018" / "provider_runtime_018.py"),
    "sys": sys,
})

assets = root / "app/src/main/assets/nexus"
main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
provider_paths = sorted(assets.glob("*provider*.js"))
assert provider_paths, "provider adapters missing"

policy_expr = '''(researchPolicy==='FORBIDDEN'
        ?'- Research policy FORBIDDEN: do not browse the web or perform external research.'
        :researchPolicy==='REQUIRED'
          ?'- Research policy REQUIRED: perform external research when available and permitted; preserve source traceability.'
          :researchPolicy==='REQUIRED_IF_STALE'
            ?'- Research policy REQUIRED_IF_STALE: perform external research when freshness or source gaps require it and it is permitted.'
            :'- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy.')'''

for p in provider_paths:
    js = p.read_text()
    js = js.replace("ALLOWED", "OPTIONAL")
    js = js.replace("      if(envelope.external_research!==false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');\n", "")
    js = js.replace("      if (envelope.external_research !== false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');\n", "")
    marker = "function buildPrompt(envelope){"
    if marker in js:
        pos = js.index(marker)
        if "const researchPolicy=" not in js[pos:pos+500]:
            js = js.replace(marker, marker + "\n    const researchPolicy=String(envelope.research_policy||'FORBIDDEN');", 1)
    for ban in [
        "'- Do NOT browse the web and do NOT perform external research.',",
        '"- Do NOT browse the web and do NOT perform external research.",',
    ]:
        if ban in js:
            js = js.replace(ban, policy_expr + ",", 1)
    js = js.replace(
        "'- Research policy OPTIONAL: external research may be used when useful and permitted.'",
        "'- Research policy OPTIONAL: external research may be used when useful and permitted by source_policy.'"
    )
    follow = "'- Follow the resolved M024 execution policy carried by the envelope.',"
    if follow in js and "Research policy OPTIONAL:" not in js:
        js = js.replace(follow, follow + policy_expr + ",", 1)
    p.write_text(js)

s = main_path.read_text()
field_anchor = "    private val nexusExchangeMonitorReportLines = mutableListOf<String>()\n"
assert field_anchor in s
s = s.replace(
    field_anchor,
    field_anchor +
    "    private var nexusExchangeMonitorReportActive = false\n"
    "    private var nexusExchangeMonitorReportTerminal = false\n"
    "    private var nexusExchangeMonitorLastProgress = \"\"\n",
    1
)

old_method_start = "    private fun appendMonitorReport(category: String, origin: String, detail: String) {\n"
start = s.index(old_method_start)
end = s.index("    private fun monitorRoute(returning: Boolean): String {\n", start)
new_method = '''    private fun appendMonitorReport(category: String, origin: String, detail: String) {
        val safeDetail = detail.replace("\\r", " ").replace("\\n", " ").take(1200)
        val provider = selectedProvider ?: "LLM"
        val line = "${System.currentTimeMillis()} | $category | $safeDetail"
        nexusExchangeMonitorReportLines.add(line)
        while (nexusExchangeMonitorReportLines.size > 80) nexusExchangeMonitorReportLines.removeAt(0)
        if (::nexusExchangeMonitorReportBody.isInitialized) {
            nexusExchangeMonitorReportBody.text =
                "Rapport des échanges NEXUS ↔ $provider\\n" +
                "Cycle courant uniquement · V-009 ARCH005 reste gelé et non modifié.\\n\\n" +
                nexusExchangeMonitorReportLines.joinToString("\\n")
            if (::nexusExchangeMonitorReportScroll.isInitialized &&
                nexusExchangeMonitorReportScroll.visibility == View.VISIBLE) {
                nexusExchangeMonitorReportScroll.post {
                    nexusExchangeMonitorReportScroll.fullScroll(android.view.View.FOCUS_DOWN)
                }
            }
        }
    }

    private fun startReadableMonitorReport() {
        nexusExchangeMonitorReportLines.clear()
        nexusExchangeMonitorReportActive = true
        nexusExchangeMonitorReportTerminal = false
        nexusExchangeMonitorLastProgress = ""
        appendMonitorReport("DÉPART", selectedProviderOrigin ?: "", "NEXUS prépare la demande.")
    }

    private fun appendProviderProgress(status: String) {
        if (!nexusExchangeMonitorReportActive || nexusExchangeMonitorReportTerminal) return
        val clean = status.replace("_", " ").trim()
        if (clean.isBlank() || clean == nexusExchangeMonitorLastProgress) return
        nexusExchangeMonitorLastProgress = clean
        appendMonitorReport("LLM", selectedProviderOrigin ?: "", clean)
    }

    private fun finishReadableMonitorReport(ok: Boolean, detail: String) {
        if (nexusExchangeMonitorReportTerminal) return
        nexusExchangeMonitorReportTerminal = true
        val label = if (ok) "TERMINÉ" else "INTERROMPU"
        appendMonitorReport(label, selectedProviderOrigin ?: "", detail)
        nexusExchangeMonitorReportActive = false
    }

'''
s = s[:start] + new_method + s[end:]
raw_phase = '        appendMonitorReport("MONITOR_PHASE", selectedProviderOrigin ?: "", "phase=$phase;detail=$detail")\n'
assert raw_phase in s
s = s.replace(raw_phase, "", 1)

start_anchor = "    private fun startExecutionProof(origin: String) {\n        monitorPreparing()\n"
assert start_anchor in s
s = s.replace(
    start_anchor,
    "    private fun startExecutionProof(origin: String) {\n"
    "        startReadableMonitorReport()\n"
    "        monitorPreparing()\n"
    "        appendMonitorReport(\"NEXUS → LLM\", origin, \"Demande prête à être transmise.\")\n",
    1
)

raw_bridge = '''            val monitorMessage = JSONObject(payload)
            appendMonitorReport("BRIDGE_MESSAGE", origin, payload)
            when (monitorMessage.optString("type")) {
'''
assert raw_bridge in s
bridge_replacement = '''            val monitorMessage = JSONObject(payload)
            val monitorType = monitorMessage.optString("type")
            if (nexusExchangeMonitorReportActive && !nexusExchangeMonitorReportTerminal) {
                when (monitorType) {
                    "PROVIDER_ACK" -> appendMonitorReport("LLM", origin, "Demande acceptée par le provider.")
                    "PROVIDER_PROGRESS" -> appendProviderProgress(monitorMessage.optString("job_status", "Traitement en cours"))
                    "PROVIDER_RESULT" -> {
                        if (monitorMessage.optBoolean("ok", false)) {
                            appendMonitorReport("LLM → NEXUS", origin, "Résultat reçu. Vérification du Result Pack en cours.")
                        } else {
                            finishReadableMonitorReport(false, safeMonitorText(monitorMessage.optString("error", "Retour LLM indisponible.")))
                        }
                    }
                }
            }
            when (monitorType) {
'''
s = s.replace(raw_bridge, bridge_replacement, 1)

raw_exec = '        appendMonitorReport("EXECUTE_JOB", origin, "job_id=$JOB_ID;job_type=${jobType.name};research_policy=${job.researchPolicy.name}")\n'
assert raw_exec in s
s = s.replace(raw_exec, '        appendMonitorReport("POLITIQUE", origin, "Recherche Web: ${job.researchPolicy.name}")\n', 1)

pass_marker = "TERMINAL_RECEIPT_PASS"
idx = s.find(pass_marker)
assert idx >= 0
pass_call = s.rfind("        monitorPass()\n", max(0, idx - 3000), idx + 3000)
assert pass_call >= 0
insert_at = pass_call + len("        monitorPass()\n")
s = s[:insert_at] + '        finishReadableMonitorReport(true, "Result Pack validé et cycle terminé.")\n' + s[insert_at:]

old_fail = '    private fun monitorFail(detail: String) = setMonitorPhase("FAIL", detail)\n'
assert old_fail in s
s = s.replace(old_fail, '''    private fun monitorFail(detail: String) {
        setMonitorPhase("FAIL", detail)
        if (nexusExchangeMonitorReportActive && !nexusExchangeMonitorReportTerminal) {
            finishReadableMonitorReport(false, safeMonitorText(detail))
        }
    }
''', 1)

main_path.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 71" in g
assert 'versionName = "0.0.71-v007-m024-u013-provider-runtime018-provider-origin-fix"' in g
g = g.replace("versionCode = 71", "versionCode = 72", 1)
g = g.replace(
    'versionName = "0.0.71-v007-m024-u013-provider-runtime018-provider-origin-fix"',
    'versionName = "0.0.72-v007-m024-u013-provider-runtime019-web-monitor-fix"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME019_BASE=RUNTIME018_PROVIDER_ORIGIN_FIX\n"
    "M024_PROVIDER_PROMPT_AUTHORITY=RESOLVED_RESEARCH_POLICY_ONLY\n"
    "M024_LEGACY_GLOBAL_WEB_BAN=REMOVED_FROM_PROVIDER_ADAPTERS\n"
    "M024_OPTIONAL_WEB=PERMITTED_WHEN_USEFUL_AND_SOURCE_POLICY_PERMITS\n"
    "MONITOR019_REPORT=READABLE_NEXUS_LLM_TIMELINE\n"
    "MONITOR019_RAW_STATUS_STREAM=NOT_EXPOSED_IN_REPORT\n"
    "MONITOR019_REPORT_SCOPE=CURRENT_EXECUTION_CYCLE_ONLY\n"
    "MONITOR019_TERMINAL_STOPS_VISIBLE_ACTIVITY=true\n"
    "RUNTIME018_PROVIDER_ORIGIN_FIX=PRESERVED\n"
    "RUNTIME014_ROTATION=PRESERVED\n"
    "RUNTIME015_COMPACT_MONITOR=PRESERVED\n"
    "V009_ARCH005=FROZEN_UNMODIFIED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

generated = main_path.read_text()
assert 'appendMonitorReport("BRIDGE_MESSAGE", origin, payload)' not in generated
assert "Rapport des échanges NEXUS ↔" in generated
assert "Cycle courant uniquement" in generated
assert "startReadableMonitorReport()" in generated
assert "finishReadableMonitorReport(true" in generated
assert "nexusExchangeMonitorReportActive = false" in generated
assert 'text = "Rapport"' in generated

for p in provider_paths:
    js = p.read_text()
    assert "Do NOT browse the web and do NOT perform external research" not in js, p.name
    assert "OPTIONAL" in js, p.name
    assert "research_policy" in js, p.name
