from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from the exact ChatGPT UIRETRY1 derivative that already passed V-005 DEVICE.
subprocess.run([
    sys.executable,
    str(repo / 'executionproof006_uiretry1' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Give V-007 its own Android sandbox and WebView profile so no V-005 app/session state is reused.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.c002.executionproof006.uiretry1"', 'applicationId = "nexus.android.v007.cleandevicee2e001"')
s = s.replace('versionCode = 10', 'versionCode = 30')
s = s.replace('versionName = "0.0.10-c002-executionproof006-uiretry1"', 'versionName = "0.0.30-v007-clean-device-e2e001"')
assert 'nexus.android.v007.cleandevicee2e001' in s
p.write_text(s)

p = work / 'app/src/main/AndroidManifest.xml'
s = p.read_text()
s = s.replace('android:label="NEXUS C002 EXECUTION PROOF 006 UIRETRY1"', 'android:label="NEXUS V007 CLEAN DEVICE E2E 001"')
assert 'NEXUS V007 CLEAN DEVICE E2E 001' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_c002_executionproof006_uiretry1': 'nexus_provider_profile_v007_clean_device_e2e_001',
    'V005-C002-EXECUTION-PROOF-006-BRIDGE-001': 'V007-CLEAN-DEVICE-E2E-001-BRIDGE-001',
    'V005-C002-EXECUTION-PROOF-006-001': 'V007-CLEAN-DEVICE-E2E-001-JOB-001',
    'V005-C002-EXECUTION-PROOF-006-COMP-001': 'V007-CLEAN-DEVICE-E2E-001-COMP-001',
    'V005_EXECUTION_PROOF_006_V1': 'V007_ANDROID_CLEAN_DEVICE_E2E_001_V1',
    'NEXUS_EXECUTION_PROOF_006_OK': 'NEXUS_V007_CLEAN_DEVICE_E2E_001_OK',
    'V005-C002-EXECUTION-PROOF-006': 'V007-ANDROID-CLEAN-DEVICE-E2E-001',
    'EXECUTION PROOF 006 — authenticate in ChatGPT; one read-only proof job will run after DESCRIBE PASS': 'V007 CLEAN DEVICE E2E 001 — authenticate in ChatGPT; one read-only job runs after DESCRIBE PASS',
    'Return the exact frozen Result Pack for this Android transport proof. The answer field must be NEXUS_EXECUTION_PROOF_006_OK.': 'Return the exact frozen Result Pack for this clean-device Android E2E proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_OK.',
    'Read-only V-005 Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation.': 'Read-only V-007 clean-device Android E2E proof. Use only the frozen package. No web research, no canonical write, no state mutation.'
}
for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new)

required = [
    'nexus_provider_profile_v007_clean_device_e2e_001',
    'V007-CLEAN-DEVICE-E2E-001-JOB-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_OK',
]
for token in required:
    assert token in s, token
p.write_text(s)

# Make the native top panel identify the clean-device gate while preserving compact UI behavior.
p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text().replace('android:text="EXECUTION PROOF 006 UIRETRY1 — initializing"', 'android:text="V007 CLEAN DEVICE E2E 001 — initializing"')
p.write_text(s)
