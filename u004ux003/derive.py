from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from validated U004 UX SHELL 002 (AUTHFIX2 + auto-close preserved).
subprocess.run([
    sys.executable,
    str(repo / 'u004ux002' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Fresh Android identity/profile for SHELL 003.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u004.uxshell002"', 'applicationId = "nexus.android.u004.uxshell003"')
s = s.replace('versionCode = 41', 'versionCode = 42')
s = s.replace('versionName = "0.0.41-u004-android-ux-shell002-autoclose"', 'versionName = "0.0.42-u004-android-ux-shell003-user-result"')
assert 'nexus.android.u004.uxshell003' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_u004_android_ux_shell_002': 'nexus_provider_profile_u004_android_ux_shell_003',
    'U004-ANDROID-UX-SHELL-002-BRIDGE-001': 'U004-ANDROID-UX-SHELL-003-BRIDGE-001',
    'U004-ANDROID-UX-SHELL-002-JOB-001': 'U004-ANDROID-UX-SHELL-003-JOB-001',
    'U004-ANDROID-UX-SHELL-002-COMP-001': 'U004-ANDROID-UX-SHELL-003-COMP-001',
    'U004_ANDROID_UX_SHELL_002_V1': 'U004_ANDROID_UX_SHELL_003_V1',
    'NEXUS_U004_ANDROID_UX_SHELL_002_OK': 'NEXUS_U004_ANDROID_UX_SHELL_003_OK',
    'U004-ANDROID-UX-SHELL-002': 'U004-ANDROID-UX-SHELL-003',
}
for old, new in replacements.items():
    s = s.replace(old, new)

# Native user result view. Provider page and raw diagnostics remain available on demand.
s = s.replace('import android.widget.PopupMenu\n', 'import android.widget.PopupMenu\nimport android.widget.LinearLayout\n')
s = s.replace(
    '    private lateinit var status: TextView\n',
    '    private lateinit var status: TextView\n    private lateinit var resultPanel: LinearLayout\n    private lateinit var resultSummary: TextView\n'
)

old_bind = '''        webView = findViewById(R.id.providerWebView)\n        status = findViewById(R.id.status)\n'''
new_bind = '''        webView = findViewById(R.id.providerWebView)\n        status = findViewById(R.id.status)\n        resultPanel = findViewById(R.id.resultPanel)\n        resultSummary = findViewById(R.id.resultSummary)\n'''
assert s.count(old_bind) == 1
s = s.replace(old_bind, new_bind)

old_menu = '''        val menuButton: Button = findViewById(R.id.nexusMenu)\n        menuButton.setOnClickListener { anchorView ->\n            val popup = PopupMenu(this, anchorView)\n            popup.menu.add(if (diagnosticExpanded) "Masquer les détails techniques" else "Détails techniques")\n            popup.setOnMenuItemClickListener {\n                diagnosticExpanded = !diagnosticExpanded\n                renderStatus()\n                true\n            }\n            popup.show()\n        }\n'''
new_menu = '''        val menuButton: Button = findViewById(R.id.nexusMenu)\n        menuButton.setOnClickListener { anchorView ->\n            val popup = PopupMenu(this, anchorView)\n            popup.menu.add(if (diagnosticExpanded) "Masquer les détails techniques" else "Détails techniques")\n            if (proofStopped) {\n                popup.menu.add(if (resultPanel.visibility == View.VISIBLE) "Voir la réponse ChatGPT" else "Afficher le résultat NEXUS")\n            }\n            popup.setOnMenuItemClickListener { item ->\n                when (item.title.toString()) {\n                    "Détails techniques", "Masquer les détails techniques" -> {\n                        diagnosticExpanded = !diagnosticExpanded\n                        renderStatus()\n                    }\n                    "Voir la réponse ChatGPT" -> showProviderResponse()\n                    "Afficher le résultat NEXUS" -> showNexusResult()\n                }\n                true\n            }\n            popup.show()\n        }\n'''
assert s.count(old_menu) == 1
s = s.replace(old_menu, new_menu)

old_terminal = '''        renderStatus()\n    }\n\n    private fun validateResultPack(job: ExecutionJob, resultPack: JSONObject): String {\n'''
new_terminal = '''        renderStatus()\n        showValidatedResult(modelRef)\n    }\n\n    private fun showValidatedResult(modelRef: String?) {\n        resultSummary.text = buildString {\n            append("La réponse du fournisseur a été reçue et validée par NEXUS.")\n            append("\\n\\nFournisseur : ChatGPT")\n            if (!modelRef.isNullOrBlank()) append("\\nSession : ").append(modelRef)\n            append("\\nStatut : Validé")\n        }\n        showNexusResult()\n    }\n\n    private fun showNexusResult() {\n        webView.visibility = View.GONE\n        resultPanel.visibility = View.VISIBLE\n    }\n\n    private fun showProviderResponse() {\n        resultPanel.visibility = View.GONE\n        webView.visibility = View.VISIBLE\n    }\n\n    private fun validateResultPack(job: ExecutionJob, resultPack: JSONObject): String {\n'''
assert s.count(old_terminal) == 1
s = s.replace(old_terminal, new_terminal)

for token in [
    'nexus_provider_profile_u004_android_ux_shell_003',
    'U004-ANDROID-UX-SHELL-003-JOB-001',
    'U004_ANDROID_UX_SHELL_003_V1',
    'NEXUS_U004_ANDROID_UX_SHELL_003_OK',
    'showValidatedResult', 'showNexusResult', 'showProviderResponse',
    'Voir la réponse ChatGPT', 'Afficher le résultat NEXUS'
]:
    assert token in s, token
p.write_text(s)

# Replace WebView-only content with WebView + native result overlay.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text()
old_web = '''    <WebView\n        android:id="@+id/providerWebView"\n        android:layout_width="match_parent"\n        android:layout_height="0dp"\n        android:layout_weight="1" />\n'''
new_web = '''    <FrameLayout\n        android:layout_width="match_parent"\n        android:layout_height="0dp"\n        android:layout_weight="1">\n\n        <WebView\n            android:id="@+id/providerWebView"\n            android:layout_width="match_parent"\n            android:layout_height="match_parent" />\n\n        <LinearLayout\n            android:id="@+id/resultPanel"\n            android:layout_width="match_parent"\n            android:layout_height="match_parent"\n            android:orientation="vertical"\n            android:gravity="center_horizontal"\n            android:paddingStart="24dp"\n            android:paddingEnd="24dp"\n            android:paddingTop="56dp"\n            android:background="#F7F7F8"\n            android:visibility="gone">\n\n            <TextView\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:text="Résultat NEXUS"\n                android:textColor="#202123"\n                android:textSize="24sp"\n                android:textStyle="bold" />\n\n            <TextView\n                android:id="@+id/resultSummary"\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="20dp"\n                android:padding="18dp"\n                android:background="#FFFFFF"\n                android:text="Résultat en attente…"\n                android:textColor="#202123"\n                android:textSize="16sp"\n                android:lineSpacingExtra="4dp" />\n\n            <TextView\n                android:layout_width="match_parent"\n                android:layout_height="wrap_content"\n                android:layout_marginTop="16dp"\n                android:text="La réponse fournisseur et les détails techniques restent accessibles depuis le menu ⋮."\n                android:textColor="#6F7075"\n                android:textSize="13sp" />\n        </LinearLayout>\n    </FrameLayout>\n'''
assert s.count(old_web) == 1
s = s.replace(old_web, new_web)
p.write_text(s)

# Hide transport diagnostic badge in normal UX, keeping it in DOM for diagnostics/proof instrumentation.
p = work / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
s = p.read_text()
old_css = """      'position:fixed','right:8px','top:8px','z-index:2147483647',\n"""
new_css = """      'display:none','position:fixed','right:8px','top:8px','z-index:2147483647',\n"""
assert s.count(old_css) == 1
s = s.replace(old_css, new_css)
assert "'display:none','position:fixed'" in s
p.write_text(s)
