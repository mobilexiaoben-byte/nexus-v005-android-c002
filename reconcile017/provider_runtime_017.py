from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

exec((repo / "reconcile016" / "provider_runtime_016.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile016" / "provider_runtime_016.py"),
    "sys": sys,
})

main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main_path.read_text()

field_anchor = "    private lateinit var nexusExchangeMonitorInfo: Button\n"
fields = """    private lateinit var nexusExchangeMonitorInfo: Button
    private lateinit var nexusExchangeMonitorReport: Button
    private lateinit var nexusExchangeMonitorReportScroll: android.widget.ScrollView
    private lateinit var nexusExchangeMonitorReportBody: TextView
    private val nexusExchangeMonitorReportLines = mutableListOf<String>()
"""
assert field_anchor in s, "Runtime016 monitor field anchor missing"
s = s.replace(field_anchor, fields, 1)

row_anchor = """        row.addView(nexusExchangeMonitor, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        row.addView(nexusExchangeMonitorInfo, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        root.addView(row, 1)
        monitorReset()
"""
row_replacement = """        nexusExchangeMonitorReportBody = TextView(this).apply {
            textSize = 10f
            setPadding(12, 10, 12, 12)
            setTextIsSelectable(true)
            typeface = android.graphics.Typeface.MONOSPACE
            text = "Diagnostic avancé NEXUS\\nV-009 ARCH005 reste gelé et non modifié.\\n"
        }
        nexusExchangeMonitorReportScroll = android.widget.ScrollView(this).apply {
            visibility = View.GONE
            isFillViewport = true
            addView(
                nexusExchangeMonitorReportBody,
                ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                )
            )
        }
        nexusExchangeMonitorReport = Button(this).apply {
            text = "Rapport"
            textSize = 10f
            minWidth = 0
            minHeight = 0
            setOnClickListener {
                val opening = nexusExchangeMonitorReportScroll.visibility != View.VISIBLE
                nexusExchangeMonitorReportScroll.visibility = if (opening) View.VISIBLE else View.GONE
                text = if (opening) "Rapport ▲" else "Rapport"
                if (opening) {
                    nexusExchangeMonitorReportScroll.post {
                        nexusExchangeMonitorReportScroll.fullScroll(android.view.View.FOCUS_DOWN)
                    }
                }
            }
        }
        row.addView(nexusExchangeMonitor, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        row.addView(nexusExchangeMonitorInfo, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        row.addView(nexusExchangeMonitorReport, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        root.addView(row, 1)
        root.addView(
            nexusExchangeMonitorReportScroll,
            2,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                (220 * resources.displayMetrics.density).toInt()
            )
        )
        appendMonitorReport("BOOT", "", "Runtime017 report panel ready; V009_ARCH005_FROZEN=true")
        monitorReset()
"""
assert row_anchor in s, "Runtime016 monitor row anchor missing"
s = s.replace(row_anchor, row_replacement, 1)

method_anchor = "    private fun monitorRoute(returning: Boolean): String {\n"
append_method = r"""    private fun appendMonitorReport(category: String, origin: String, detail: String) {
        val safeDetail = detail.replace("\r", " ").replace("\n", " ").take(4000)
        val safeOrigin = origin.replace("\r", " ").replace("\n", " ").take(512)
        val line = "${System.currentTimeMillis()} | $category | ${selectedProvider ?: "LLM"} | $safeOrigin | $safeDetail"
        nexusExchangeMonitorReportLines.add(line)
        while (nexusExchangeMonitorReportLines.size > 200) nexusExchangeMonitorReportLines.removeAt(0)
        if (::nexusExchangeMonitorReportBody.isInitialized) {
            nexusExchangeMonitorReportBody.text =
                "Diagnostic avancé NEXUS\nV-009 ARCH005 reste gelé et non modifié.\n" +
                nexusExchangeMonitorReportLines.joinToString("\n")
            if (::nexusExchangeMonitorReportScroll.isInitialized &&
                nexusExchangeMonitorReportScroll.visibility == View.VISIBLE) {
                nexusExchangeMonitorReportScroll.post {
                    nexusExchangeMonitorReportScroll.fullScroll(android.view.View.FOCUS_DOWN)
                }
            }
        }
    }

"""
assert method_anchor in s, "monitorRoute anchor missing"
s = s.replace(method_anchor, append_method + method_anchor, 1)

phase_anchor = """        monitorPhase = phase
        monitorDetail = detail
"""
phase_replacement = """        monitorPhase = phase
        monitorDetail = detail
        appendMonitorReport("MONITOR_PHASE", selectedProviderOrigin ?: "", "phase=$phase;detail=$detail")
"""
assert phase_anchor in s, "setMonitorPhase anchor missing"
s = s.replace(phase_anchor, phase_replacement, 1)

bridge_anchor = """            val monitorMessage = JSONObject(payload)
            when (monitorMessage.optString("type")) {
"""
bridge_replacement = """            val monitorMessage = JSONObject(payload)
            appendMonitorReport("BRIDGE_MESSAGE", origin, payload)
            when (monitorMessage.optString("type")) {
"""
assert bridge_anchor in s, "bridge monitor anchor missing"
s = s.replace(bridge_anchor, bridge_replacement, 1)

diag_anchor = 'recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;job_type=${jobType.name};research_policy=${job.researchPolicy.name}")'
assert diag_anchor in s, "Runtime016 execution diagnostic anchor missing"
s = s.replace(
    diag_anchor,
    diag_anchor + '\n        appendMonitorReport("EXECUTE_JOB", origin, "job_id=$JOB_ID;job_type=${jobType.name};research_policy=${job.researchPolicy.name}")',
    1
)

main_path.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 69" in g
assert 'versionName = "0.0.69-v007-m024-u013-provider-runtime016-policy-router-fix"' in g
g = g.replace("versionCode = 69", "versionCode = 70", 1)
g = g.replace(
    'versionName = "0.0.69-v007-m024-u013-provider-runtime016-policy-router-fix"',
    'versionName = "0.0.70-v007-m024-u013-provider-runtime017-report-panel"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME017_BASE=RUNTIME016_POLICY_ROUTER_FIX\n"
    "MONITOR017_COMPACT=PRESERVED_FROM_RUNTIME015\n"
    "MONITOR017_REPORT_BUTTON=RIGHT_OF_COMPACT_MONITOR\n"
    "MONITOR017_REPORT_PANEL=HIDDEN_BY_DEFAULT_SCROLLABLE_220DP\n"
    "MONITOR017_REPORT_SOURCE=ANDROID_EXISTING_DIAGNOSTICS_PLUS_BRIDGE_RAW_EVENTS\n"
    "MONITOR017_REPORT_RETENTION=200_LINES_BOUNDED\n"
    "M024_RUNTIME016_POLICY_ROUTER=PRESERVED\n"
    "RUNTIME014_ROTATION=PRESERVED\n"
    "V009_ARCH005=FROZEN_UNMODIFIED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

generated = main_path.read_text()
for token in [
    'text = "Rapport"',
    'nexusExchangeMonitorReportScroll.visibility = if (opening) View.VISIBLE else View.GONE',
    'android.widget.ScrollView',
    '(220 * resources.displayMetrics.density).toInt()',
    'appendMonitorReport("BRIDGE_MESSAGE", origin, payload)',
    'appendMonitorReport("EXECUTE_JOB", origin, "job_id=$JOB_ID;job_type=${jobType.name};research_policy=${job.researchPolicy.name}")',
    'CONFIGURATION_CHANGED_PRESERVED',
    'setupExchangeMonitor()',
]:
    assert token in generated, token
transport = (root / "app/src/main/java/nexus/android/c002/core/TransportContract.kt").read_text()
assert 'JobType.OPEN_ANALYSIS -> ResearchPolicy.OPTIONAL' in transport
assert 'versionCode = 70' in gradle.read_text()
