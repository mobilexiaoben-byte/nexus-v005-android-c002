from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Preserve the V007 AUTHFIX2 transport/auth path exactly, then apply UX-only shell changes.
subprocess.run([
    sys.executable,
    str(repo / 'v007authfix2' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Fresh Android sandbox/profile for U-004 user-review candidate.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.cleandevicee2e001.authfix2"', 'applicationId = "nexus.android.u004.uxshell001"')
s = s.replace('versionCode = 32', 'versionCode = 40')
s = s.replace('versionName = "0.0.32-v007-clean-device-e2e001-authfix2"', 'versionName = "0.0.40-u004-android-ux-shell001"')
assert 'nexus.android.u004.uxshell001' in s
p.write_text(s)

p = work / 'app/src/main/AndroidManifest.xml'
s = p.read_text().replace('android:label="NEXUS V007 CLEAN DEVICE AUTHFIX2"', 'android:label="NEXUS"')
assert 'android:label="NEXUS"' in s
p.write_text(s)

# UX shell: minimal NEXUS header + provider badge + user-readable status.
layout = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:background="#F7F7F8">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="56dp"
        android:orientation="horizontal"
        android:gravity="center_vertical"
        android:paddingStart="16dp"
        android:paddingEnd="8dp"
        android:background="#FFFFFF">

        <TextView
            android:id="@+id/nexusTitle"
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:text="NEXUS"
            android:textColor="#202123"
            android:textSize="18sp"
            android:textStyle="bold"
            android:letterSpacing="0.12" />

        <TextView
            android:id="@+id/providerBadge"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:paddingStart="10dp"
            android:paddingEnd="10dp"
            android:paddingTop="6dp"
            android:paddingBottom="6dp"
            android:text="ChatGPT"
            android:textColor="#6F7075"
            android:textSize="13sp" />

        <Button
            android:id="@+id/nexusMenu"
            android:layout_width="48dp"
            android:layout_height="48dp"
            android:background="@android:color/transparent"
            android:text="⋮"
            android:textColor="#202123"
            android:textSize="24sp"
            android:contentDescription="Menu NEXUS" />
    </LinearLayout>

    <View
        android:layout_width="match_parent"
        android:layout_height="1dp"
        android:background="#E5E5E7" />

    <TextView
        android:id="@+id/status"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:minHeight="48dp"
        android:gravity="center_vertical"
        android:paddingStart="16dp"
        android:paddingEnd="16dp"
        android:paddingTop="10dp"
        android:paddingBottom="10dp"
        android:maxLines="2"
        android:ellipsize="end"
        android:clickable="true"
        android:focusable="true"
        android:background="#FFFFFF"
        android:text="Connexion au fournisseur…"
        android:textColor="#202123"
        android:textSize="14sp" />

    <View
        android:layout_width="match_parent"
        android:layout_height="1dp"
        android:background="#E5E5E7" />

    <WebView
        android:id="@+id/providerWebView"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1" />
</LinearLayout>
'''
(work / 'app/src/main/res/layout/activity_main.xml').write_text(layout)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_v007_clean_device_e2e_001_authfix2': 'nexus_provider_profile_u004_android_ux_shell_001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-BRIDGE-001': 'U004-ANDROID-UX-SHELL-001-BRIDGE-001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-JOB-001': 'U004-ANDROID-UX-SHELL-001-JOB-001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-COMP-001': 'U004-ANDROID-UX-SHELL-001-COMP-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX2_V1': 'U004_ANDROID_UX_SHELL_001_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX2_OK': 'NEXUS_U004_ANDROID_UX_SHELL_001_OK',
    'V007-ANDROID-CLEAN-DEVICE-E2E-001-AUTHFIX2': 'U004-ANDROID-UX-SHELL-001',
    'V007 AUTHFIX2 — authenticate in ChatGPT; NEXUS may open the ChatGPT sidebar only to expose authoritative auth evidence': 'U004 UX — connexion au fournisseur',
    'Read-only V-007 clean-device Android E2E proof. Use only the frozen package. No web research, no canonical write, no state mutation.': 'Read-only U-004 Android UX transport-regression proof. Use only the frozen package. No web research, no canonical write, no state mutation.',
}
for old, new in replacements.items():
    s = s.replace(old, new)

# Add PopupMenu import without touching bridge/transport imports.
s = s.replace('import android.widget.TextView\n', 'import android.widget.TextView\nimport android.widget.Button\nimport android.widget.PopupMenu\n')

# Wire the UX menu after status binding.
anchor = '''        status = findViewById(R.id.status)\n        status.setOnClickListener {\n            diagnosticExpanded = !diagnosticExpanded\n            renderStatus()\n        }\n'''
replacement = '''        status = findViewById(R.id.status)\n        status.setOnClickListener {\n            diagnosticExpanded = !diagnosticExpanded\n            renderStatus()\n        }\n        val menuButton: Button = findViewById(R.id.nexusMenu)\n        menuButton.setOnClickListener { anchorView ->\n            val popup = PopupMenu(this, anchorView)\n            popup.menu.add(if (diagnosticExpanded) "Masquer les détails techniques" else "Détails techniques")\n            popup.setOnMenuItemClickListener {\n                diagnosticExpanded = !diagnosticExpanded\n                renderStatus()\n                true\n            }\n            popup.show()\n        }\n'''
assert s.count(anchor) == 1, 'status binding anchor mismatch'
s = s.replace(anchor, replacement)

# Present user-readable states by default; raw diagnostics remain available on demand.
old_render = '''    private fun renderStatus() {\n        status.maxLines = if (diagnosticExpanded) EXPANDED_STATUS_LINES else COMPACT_STATUS_LINES\n        status.text = buildString {\n            append(currentHeadline)\n            val visibleEvents = if (diagnosticExpanded) diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT) else diagnosticEvents.takeLast(1)\n            visibleEvents.forEach { event ->\n                append("\\n").append(event.line)\n                if (event.repeatCount > 1) append(" ×").append(event.repeatCount)\n            }\n            if (diagnosticExpanded && !currentBody.isNullOrBlank()) append("\\n").append(currentBody)\n        }\n    }\n'''
new_render = '''    private fun friendlyHeadline(raw: String): String = when {\n        raw.startsWith("AUTH REQUIRED") -> "Connexion à ChatGPT requise"\n        raw.startsWith("DESCRIBE PASS") -> "Connecté · préparation de NEXUS"\n        raw.startsWith("ACK PASS") -> "Requête envoyée · analyse en cours"\n        raw.startsWith("EXECUTION PROOF PASS") -> "Terminé · résultat validé"\n        raw.startsWith("EXECUTION PROOF") -> "Analyse en cours…"\n        raw.startsWith("BLOCKED") -> "Exécution bloquée · vérification de sécurité"\n        raw.startsWith("U004 UX") -> "Connexion au fournisseur…"\n        else -> raw\n    }\n\n    private fun renderStatus() {\n        status.maxLines = if (diagnosticExpanded) EXPANDED_STATUS_LINES else COMPACT_STATUS_LINES\n        status.text = buildString {\n            append(friendlyHeadline(currentHeadline))\n            if (diagnosticExpanded) {\n                append("\\n").append(currentHeadline)\n                diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT).forEach { event ->\n                    append("\\n").append(event.line)\n                    if (event.repeatCount > 1) append(" ×").append(event.repeatCount)\n                }\n                if (!currentBody.isNullOrBlank()) append("\\n").append(currentBody)\n            }\n        }\n    }\n'''
assert s.count(old_render) == 1, 'renderStatus anchor mismatch'
s = s.replace(old_render, new_render)

for token in [
    'nexus_provider_profile_u004_android_ux_shell_001',
    'U004-ANDROID-UX-SHELL-001-JOB-001',
    'U004_ANDROID_UX_SHELL_001_V1',
    'NEXUS_U004_ANDROID_UX_SHELL_001_OK',
    'friendlyHeadline',
    'PopupMenu',
]:
    assert token in s, token
p.write_text(s)
