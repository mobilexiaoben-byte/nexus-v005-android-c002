from pathlib import Path
import re
import shutil
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

exec((repo / "reconcile014" / "provider_runtime_014.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile014" / "provider_runtime_014.py"),
    "sys": sys,
})

assets = root / "app/src/main/assets/nexus"
monitor_source = repo / "reconcile015" / "nexus_existing_guest_monitor_patch.js"
assert monitor_source.exists(), "historical compact monitor source missing"
shutil.copy2(monitor_source, assets / "nexus_existing_guest_monitor_patch.js")

main = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main.read_text()

def add_import(import_line):
    global s
    if import_line not in s:
        marker = "import android.app.Activity\n"
        assert marker in s, "Activity import anchor missing"
        s = s.replace(marker, marker + import_line + "\n", 1)

for imp in [
    "import android.text.TextUtils",
    "import android.view.Gravity",
]:
    add_import(imp)

field_anchor = "    private lateinit var productState: TextView\n"
assert field_anchor in s, "productState field anchor missing"
fields = """    private lateinit var productState: TextView
    private lateinit var nexusExchangeMonitor: TextView
    private lateinit var nexusExchangeMonitorInfo: Button
    private var monitorPhase: String = "IDLE"
    private var monitorDetail: String = ""
    private var monitorChaserIndex: Int = 0
    private var monitorDirection: Int = 1
    private val monitorChaser = object : Runnable {
        override fun run() {
            renderExchangeMonitor()
            if (monitorPhase == "OUTBOUND" || monitorPhase == "RETURNING") {
                monitorChaserIndex = (monitorChaserIndex + monitorDirection + 8) % 8
                handler.postDelayed(this, 100L)
            }
        }
    }
"""
s = s.replace(field_anchor, fields, 1)

bind_anchor = "        productState = findViewById(R.id.productState)\n"
assert bind_anchor in s, "productState binding anchor missing"
s = s.replace(bind_anchor, bind_anchor + "        setupExchangeMonitor()\n", 1)

method_anchor = "    private fun resetExecutionAttempt(reason: String) {\n"
assert method_anchor in s, "resetExecutionAttempt anchor missing"
monitor_methods = r'''    private fun safeMonitorText(detail: String): String {
        val value = detail.removePrefix("Error: ").trim()
        return when {
            value.contains("NOT_AUTHENTICATED", true) || value.contains("SESSION_NOT_AUTHENTICATED", true) ->
                "La session du LLM sélectionné n’est pas authentifiée."
            value.contains("TAB_NOT_FOUND", true) -> "L’onglet du LLM sélectionné n’est pas ouvert."
            value.contains("TIMEOUT", true) -> "Le LLM n’a pas renvoyé de résultat dans le délai prévu."
            value.contains("CORRELATION", true) || value.contains("MISMATCH", true) || value.contains("FINGERPRINT", true) ->
                "Le résultat reçu ne correspond pas exactement à la demande envoyée."
            value.contains("RESULT_PACK", true) -> "Le résultat reçu ne respecte pas le format attendu par NEXUS."
            value.contains("ANOTHER_V001_JOB_ACTIVE", true) -> "Une autre analyse NEXUS est déjà en cours."
            value.contains("BRIDGE_UNAVAILABLE", true) || value.contains("AUTHORIZED_CLIENT_BRIDGE_UNAVAILABLE", true) ->
                "Le lien local entre NEXUS et le LLM n’est pas disponible."
            value.isNotBlank() -> value
            else -> "Le parcours observé n’a pas pu être validé."
        }
    }

    private fun setupExchangeMonitor() {
        val root = findViewById<LinearLayout>(R.id.rootShell)
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(18, 8, 12, 8)
        }
        nexusExchangeMonitor = TextView(this).apply {
            textSize = 11f
            setPadding(4, 4, 8, 4)
            isSingleLine = true
            ellipsize = TextUtils.TruncateAt.END
        }
        nexusExchangeMonitorInfo = Button(this).apply {
            text = "ⓘ"
            textSize = 14f
            minWidth = 0
            minHeight = 0
            visibility = View.GONE
            setOnClickListener {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("Erreur détectée")
                    .setMessage(safeMonitorText(monitorDetail))
                    .setPositiveButton("OK", null)
                    .show()
            }
        }
        row.addView(nexusExchangeMonitor, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        row.addView(nexusExchangeMonitorInfo, LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT))
        root.addView(row, 1)
        monitorReset()
    }

    private fun monitorRoute(returning: Boolean): String {
        val items = MutableList(8) { "›" }
        val index = monitorChaserIndex.coerceIn(0, 7)
        items[index] = "▶"
        return items.joinToString(" ")
    }

    private fun renderExchangeMonitor() {
        if (!::nexusExchangeMonitor.isInitialized) return
        val provider = selectedProvider ?: "LLM"
        val route = monitorRoute(monitorPhase == "RETURNING")
        val text = when (monitorPhase) {
            "PREPARING" -> "SURVEILLANCE ACTIVE · 🔵 NEXUS  › › › › › › › ›  ⚪ $provider · Préparation · Surveillance active"
            "OUTBOUND" -> "SURVEILLANCE ACTIVE · 🔵 NEXUS  $route  ⚪ $provider · NEXUS vers LLM · Surveillance active"
            "PROVIDER" -> "SURVEILLANCE ACTIVE · ⚪ NEXUS  › › › › › › › ›  🔵 $provider · Traitement LLM · Surveillance active"
            "RETURNING" -> "SURVEILLANCE ACTIVE · 🔵 NEXUS  $route  🟢 $provider · LLM vers NEXUS · Vérification en cours"
            "PASS" -> "SURVEILLANCE ACTIVE · 🟢 NEXUS  › › › › › › › ›  🟢 $provider · Terminé · Échange conforme"
            "FAIL" -> "SURVEILLANCE ACTIVE · 🔴 NEXUS  › › › › › › › ›  🔴 $provider · Interrompu · Erreur détectée"
            else -> "SURVEILLANCE ACTIVE · ⚪ NEXUS  › › › › › › › ›  ⚪ $provider · En attente · Prêt"
        }
        nexusExchangeMonitor.text = text
        nexusExchangeMonitorInfo.visibility = if (monitorPhase == "FAIL") View.VISIBLE else View.GONE
    }

    private fun setMonitorPhase(phase: String, detail: String = "") {
        handler.removeCallbacks(monitorChaser)
        monitorPhase = phase
        monitorDetail = detail
        monitorDirection = if (phase == "RETURNING") -1 else 1
        monitorChaserIndex = if (phase == "RETURNING") 7 else 0
        renderExchangeMonitor()
        if (phase == "OUTBOUND" || phase == "RETURNING") handler.post(monitorChaser)
    }

    private fun monitorReset() = setMonitorPhase("IDLE")
    private fun monitorPreparing() = setMonitorPhase("PREPARING")
    private fun monitorOutbound() = setMonitorPhase("OUTBOUND")
    private fun monitorProvider() = setMonitorPhase("PROVIDER")
    private fun monitorReturning() = setMonitorPhase("RETURNING")
    private fun monitorPass() = setMonitorPhase("PASS")
    private fun monitorFail(detail: String) = setMonitorPhase("FAIL", detail)

'''
s = s.replace(method_anchor, monitor_methods + method_anchor, 1)
s = s.replace(method_anchor, method_anchor + '        monitorReset()\n', 1)

start_anchor = "    private fun startExecutionProof(origin: String) {\n"
assert start_anchor in s, "startExecutionProof anchor missing"
s = s.replace(start_anchor, start_anchor + '        monitorPreparing()\n', 1)

posted = '            else recordDiagnostic("EXECUTE_JOB_POSTED", normalizedOrigin, "bridge_ready=true;attempt=$attempt")\n'
assert posted in s, "EXECUTE_JOB_POSTED anchor missing"
s = s.replace(posted, '            else {\n                monitorOutbound()\n                recordDiagnostic("EXECUTE_JOB_POSTED", normalizedOrigin, "bridge_ready=true;attempt=$attempt")\n            }\n', 1)

bridge_anchor = "    private fun handleBridgeMessage(origin: String, payload: String) {\n"
assert bridge_anchor in s, "handleBridgeMessage anchor missing"
bridge_observer = '''    private fun handleBridgeMessage(origin: String, payload: String) {
        runCatching {
            val monitorMessage = JSONObject(payload)
            when (monitorMessage.optString("type")) {
                "PROVIDER_ACK", "PROVIDER_PROGRESS" -> monitorProvider()
                "PROVIDER_RESULT" -> if (monitorMessage.optBoolean("ok", false)) monitorReturning()
            }
        }
'''
s = s.replace(bridge_anchor, bridge_observer, 1)

block_re = re.compile(r'(\n\s*private fun block\(reason: String\) \{\n)')
m = block_re.search(s)
assert m, "block(reason) method anchor missing"
s = s[:m.end()] + '        monitorFail(reason)\n' + s[m.end():]

pass_marker = 'TERMINAL_RECEIPT_PASS'
idx = s.find(pass_marker)
assert idx >= 0, "terminal PASS marker missing"
assignment = s.rfind('terminalReceived = true', max(0, idx - 2500), idx + 2500)
assert assignment >= 0, "terminalReceived PASS assignment missing near marker"
line_end = s.find('\n', assignment)
s = s[:line_end + 1] + '        monitorPass()\n' + s[line_end + 1:]

main.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 67" in g
assert 'versionName = "0.0.67-v007-m024-u013-provider-runtime014-rotation-preserve"' in g
g = g.replace("versionCode = 67", "versionCode = 68", 1)
g = g.replace(
    'versionName = "0.0.67-v007-m024-u013-provider-runtime014-rotation-preserve"',
    'versionName = "0.0.68-v007-m024-u013-provider-runtime015-monitor-integrated"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME015_BASE=RUNTIME014_ROTATION_PRESERVE\n"
    "MONITOR015_SOURCE=nexus_existing_guest_monitor_patch.js\n"
    "MONITOR015_SOURCE_ROLE=BYTE_PRESERVED_APK_ASSET_PLUS_NATIVE_ANDROID_ADAPTER\n"
    "MONITOR015_STATES=IDLE,PREPARING,OUTBOUND,PROVIDER,RETURNING,PASS,FAIL\n"
    "MONITOR015_ERROR_DETAIL=USER_SAFE_INFO_DIALOG\n"
    "MONITOR015_V009=FROZEN_UNMODIFIED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

generated = main.read_text()
for token in [
    "setupExchangeMonitor()",
    "monitorOutbound()",
    "monitorProvider()",
    "monitorReturning()",
    "monitorPass()",
    "monitorFail(reason)",
    "Erreur détectée",
    "SURVEILLANCE ACTIVE",
]:
    assert token in generated, token
assert (assets / "nexus_existing_guest_monitor_patch.js").read_text() == monitor_source.read_text()
