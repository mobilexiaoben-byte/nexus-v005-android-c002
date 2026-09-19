from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from validated U004 UX SHELL 003 (AUTHFIX2 + auto-close + native result view preserved).
subprocess.run([
    sys.executable,
    str(repo / 'u004ux003' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Fresh Android identity/profile for SHELL 004.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u004.uxshell003"', 'applicationId = "nexus.android.u004.uxshell004"')
s = s.replace('versionCode = 42', 'versionCode = 43')
s = s.replace('versionName = "0.0.42-u004-android-ux-shell003-user-result"', 'versionName = "0.0.43-u004-android-ux-shell004-content"')
assert 'nexus.android.u004.uxshell004' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_u004_android_ux_shell_003': 'nexus_provider_profile_u004_android_ux_shell_004',
    'U004-ANDROID-UX-SHELL-003-BRIDGE-001': 'U004-ANDROID-UX-SHELL-004-BRIDGE-001',
    'U004-ANDROID-UX-SHELL-003-JOB-001': 'U004-ANDROID-UX-SHELL-004-JOB-001',
    'U004-ANDROID-UX-SHELL-003-COMP-001': 'U004-ANDROID-UX-SHELL-004-COMP-001',
    'U004_ANDROID_UX_SHELL_003_V1': 'U004_ANDROID_UX_SHELL_004_V1',
    'NEXUS_U004_ANDROID_UX_SHELL_003_OK': "Le résultat NEXUS utile est affiché directement dans l'application Android après validation.",
    'U004-ANDROID-UX-SHELL-003': 'U004-ANDROID-UX-SHELL-004',
}
for old, new in replacements.items():
    s = s.replace(old, new)

old_call = '        showValidatedResult(modelRef)\n'
new_call = '        showValidatedResult(resultPack.optString("answer"), modelRef)\n'
assert s.count(old_call) == 1, 'showValidatedResult call mismatch'
s = s.replace(old_call, new_call)

old_fn = '''    private fun showValidatedResult(modelRef: String?) {\n        resultSummary.text = buildString {\n            append("La réponse du fournisseur a été reçue et validée par NEXUS.")\n            append("\\n\\nFournisseur : ChatGPT")\n            if (!modelRef.isNullOrBlank()) append("\\nSession : ").append(modelRef)\n            append("\\nStatut : Validé")\n        }\n        showNexusResult()\n    }\n'''
new_fn = '''    private fun showValidatedResult(answer: String, modelRef: String?) {\n        val userAnswer = answer.trim()\n        resultSummary.text = buildString {\n            append(userAnswer.ifBlank { "Résultat validé, contenu vide." })\n            append("\\n\\nValidé par NEXUS · ChatGPT")\n        }\n        showNexusResult()\n    }\n'''
assert s.count(old_fn) == 1, 'showValidatedResult body mismatch'
s = s.replace(old_fn, new_fn)

# Update the proof question so the validated answer itself is a readable user-facing result.
old_q = 'const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android transport proof. The answer field must be Le résultat NEXUS utile est affiché directement dans l\'application Android après validation."'
if old_q not in s:
    old_q = 'const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android transport proof. The answer field must be Le résultat NEXUS utile est affiché directement dans l\'application Android après validation."'
# Literal replacement above already transformed the old token inside PROOF_QUESTION. Keep wording but verify readable expected answer is present.

for token in [
    'nexus_provider_profile_u004_android_ux_shell_004',
    'U004-ANDROID-UX-SHELL-004-JOB-001',
    'U004_ANDROID_UX_SHELL_004_V1',
    "Le résultat NEXUS utile est affiché directement dans l'application Android après validation.",
    'showValidatedResult(resultPack.optString("answer"), modelRef)',
    'private fun showValidatedResult(answer: String, modelRef: String?)',
    'append(userAnswer.ifBlank { "Résultat validé, contenu vide." })',
    'Validé par NEXUS · ChatGPT',
    'Voir la réponse ChatGPT',
    'Afficher le résultat NEXUS',
]:
    assert token in s, token
p.write_text(s)

# SHELL 004 makes the content hierarchy explicit without exposing technical session text in the main card.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text()
s = s.replace('android:text="Résultat NEXUS"', 'android:text="Résultat NEXUS"')
s = s.replace('android:text="Résultat en attente…"', 'android:text="Contenu du résultat en attente…"')
p.write_text(s)
