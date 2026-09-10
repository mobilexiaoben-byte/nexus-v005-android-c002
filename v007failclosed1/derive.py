from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from AUTHFIX2 so the already-proved autonomous auth/menu behavior is preserved.
subprocess.run([
    sys.executable,
    str(repo / 'v007authfix2' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Fresh sandbox/profile: this is a test-only fault-injection candidate, not a production transport change.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.cleandevicee2e001.authfix2"', 'applicationId = "nexus.android.v007.cleandevicee2e001.failclosed1"')
s = s.replace('versionCode = 32', 'versionCode = 33')
s = s.replace('versionName = "0.0.32-v007-clean-device-e2e001-authfix2"', 'versionName = "0.0.33-v007-clean-device-e2e001-failclosed1"')
assert 'nexus.android.v007.cleandevicee2e001.failclosed1' in s
p.write_text(s)

p = work / 'app/src/main/AndroidManifest.xml'
s = p.read_text().replace('android:label="NEXUS V007 CLEAN DEVICE AUTHFIX2"', 'android:label="NEXUS V007 FAIL-CLOSED 1"')
assert 'NEXUS V007 FAIL-CLOSED 1' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()
replacements = {
    'nexus_provider_profile_v007_clean_device_e2e_001_authfix2': 'nexus_provider_profile_v007_clean_device_e2e_001_failclosed1',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-BRIDGE-001': 'V007-CLEAN-DEVICE-E2E-001-FAILCLOSED1-BRIDGE-001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-JOB-001': 'V007-CLEAN-DEVICE-E2E-001-FAILCLOSED1-JOB-001',
    'V007-CLEAN-DEVICE-E2E-001-AUTHFIX2-COMP-001': 'V007-CLEAN-DEVICE-E2E-001-FAILCLOSED1-COMP-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_AUTHFIX2_V1': 'V007_ANDROID_CLEAN_DEVICE_E2E_001_FAILCLOSED1_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX2_OK': 'NEXUS_V007_CLEAN_DEVICE_E2E_001_FAILCLOSED1_EXPECTED_OK',
    'V007-ANDROID-CLEAN-DEVICE-E2E-001-AUTHFIX2': 'V007-ANDROID-CLEAN-DEVICE-E2E-001-FAILCLOSED1',
    'V007 AUTHFIX2 — authenticate in ChatGPT; NEXUS may open the ChatGPT sidebar only to expose authoritative auth evidence': 'V007 FAIL-CLOSED 1 — deterministic result corruption must be rejected locally',
    'Return the exact frozen Result Pack for this V007 AUTHFIX2 proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_AUTHFIX2_OK.': 'Return the exact frozen Result Pack for this V007 fail-closed proof. The answer field must be NEXUS_V007_CLEAN_DEVICE_E2E_001_FAILCLOSED1_EXPECTED_OK.',
}
for old, new in replacements.items():
    s = s.replace(old, new)

# Inject a deterministic corruption AFTER extraction and BEFORE local validation.
# This is the controlled fault under test. A false PASS would be a V-007 failure.
anchor = '''        val packValidation = validateResultPack(job, resultPack)\n'''
injection = '''        val originalAnswerBeforeFault = resultPack.optString("answer")\n        recordDiagnostic("FAILCLOSED_FAULT_INJECTED", CHATGPT_ORIGIN, "field=answer;original=" + sanitizeCode(originalAnswerBeforeFault))\n        resultPack.put("answer", FAILCLOSED_INJECTED_ANSWER)\n\n        val packValidation = validateResultPack(job, resultPack)\n'''
assert s.count(anchor) == 1, 'result validation anchor mismatch'
s = s.replace(anchor, injection)

const_anchor = '        const val PROOF_TOKEN = "NEXUS_V007_CLEAN_DEVICE_E2E_001_FAILCLOSED1_EXPECTED_OK"\n'
const_new = const_anchor + '        const val FAILCLOSED_INJECTED_ANSWER = "NEXUS_V007_FAILCLOSED_INJECTED_WRONG_ANSWER"\n'
assert s.count(const_anchor) == 1, 'PROOF_TOKEN constant anchor mismatch'
s = s.replace(const_anchor, const_new)

for token in [
    'nexus_provider_profile_v007_clean_device_e2e_001_failclosed1',
    'V007-CLEAN-DEVICE-E2E-001-FAILCLOSED1-JOB-001',
    'V007_ANDROID_CLEAN_DEVICE_E2E_001_FAILCLOSED1_V1',
    'NEXUS_V007_CLEAN_DEVICE_E2E_001_FAILCLOSED1_EXPECTED_OK',
    'NEXUS_V007_FAILCLOSED_INJECTED_WRONG_ANSWER',
    'FAILCLOSED_FAULT_INJECTED',
    'ANDROID_RESULT_ANSWER_MISMATCH',
]:
    assert token in s, token
p.write_text(s)

p = work / 'app/src/main/res/layout/activity_main.xml'
s = p.read_text().replace('android:text="V007 CLEAN DEVICE AUTHFIX2 — initializing"', 'android:text="V007 FAIL-CLOSED 1 — initializing"')
p.write_text(s)
