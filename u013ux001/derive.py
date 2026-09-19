from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from validated U004 SHELL 004: proven Android transport + native NEXUS result view.
subprocess.run([
    sys.executable,
    str(repo / 'u004ux004' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# U-013 shared UX Android candidate identity. Runtime behavior is inherited unchanged.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u004.uxshell004"', 'applicationId = "nexus.android.u013.shared001"')
s = s.replace('versionCode = 43', 'versionCode = 46')
s = s.replace('versionName = "0.0.43-u004-android-ux-shell004-content"', 'versionName = "0.0.46-u013-android-ux-shared001"')
assert 'nexus.android.u013.shared001' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_u004_android_ux_shell_004': 'nexus_provider_profile_u013_android_shared_001',
    'U004-ANDROID-UX-SHELL-004-BRIDGE-001': 'U013-ANDROID-UX-SHARED-001-BRIDGE-001',
    'U004-ANDROID-UX-SHELL-004-JOB-001': 'U013-ANDROID-UX-SHARED-001-JOB-001',
    'U004-ANDROID-UX-SHELL-004-COMP-001': 'U013-ANDROID-UX-SHARED-001-COMP-001',
    'U004_ANDROID_UX_SHELL_004_V1': 'U013_ANDROID_UX_SHARED_001_V1',
    'U004-ANDROID-UX-SHELL-004': 'U013-ANDROID-UX-SHARED-001',
    'Validé par NEXUS · ChatGPT': 'Validé par NEXUS · fournisseur en arrière-plan',
}
for old, new in replacements.items():
    s = s.replace(old, new)

for token in [
    'nexus_provider_profile_u013_android_shared_001',
    'U013-ANDROID-UX-SHARED-001-JOB-001',
    'U013_ANDROID_UX_SHARED_001_V1',
    'Validé par NEXUS · fournisseur en arrière-plan',
]:
    assert token in s, token
p.write_text(s)

# Shared UX presentation layer: NEXUS-first, provider-secondary, clear baseline identity.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text()
s = s.replace('android:text="Résultat NEXUS"', 'android:text="NEXUS"')
s = s.replace('android:text="Contenu du résultat en attente…"', 'android:text="Résultat en attente…"')
s = s.replace(
    'android:text="La réponse fournisseur et les détails techniques restent accessibles depuis le menu ⋮."',
    'android:text="BASELINE_UX_SHARED_001 · Le fournisseur LLM et les détails techniques restent accessibles depuis le menu ⋮."'
)
p.write_text(s)

# Build-time baseline lock for traceability.
lock = work / 'U013_BASELINE_LOCK.txt'
lock.write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'DESIGN_BASELINE_DRIVE=19cINcqyLSyoshqeRh-SeOlKoTaFoXFOrs31Hu--J54g\n'
    'RUNTIME_BASELINE=U004_ANDROID_UX_SHELL_004\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_001\n'
    'NON_MODIFIED_ORIGINALS=transport,auth,bridge,result_pack,fail_closed\n'
)
