from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
subprocess.run([sys.executable, str(repo / 'u013ux007' / 'derive.py'), str(repo), str(work)], check=True)

p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared007"', 'applicationId = "nexus.android.u013.shared008"')
s = s.replace('versionCode = 52', 'versionCode = 53')
s = s.replace('versionName = "0.0.52-u013-android-ux-shared007-o24-bridge"', 'versionName = "0.0.53-u013-android-ux-shared008-o24-visible-state"')
assert 'nexus.android.u013.shared008' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

s = s.replace(
    '        productState.text = "Fact Check · transmission O24…"\n',
    '        productState.text = "FACT CHECK O24 · transmission…\\nJob : $jobId"\n'
)

old = '''                        result == "ACCEPTED" && status == "PENDING_RESEARCH" && !engineCalled ->
                            "Fact Check transmis · recherche externe en attente"
'''
new = '''                        result == "ACCEPTED" && status == "PENDING_RESEARCH" && !engineCalled ->
                            "FACT CHECK O24 · TRANSMIS\\nJob : $returnedJob\\nÉtat : PENDING_RESEARCH\\nRecherche externe en attente"
'''
assert s.count(old) == 1
s = s.replace(old, new)

s = s.replace(
    '                        errorCode.isNotBlank() -> "Fact Check · $errorCode"\n',
    '                        errorCode.isNotBlank() -> "FACT CHECK O24 · $errorCode\\nJob : $returnedJob"\n'
)
s = s.replace(
    '                        else -> "Fact Check · $result $status".trim()\n',
    '                        else -> "FACT CHECK O24 · $result $status\\nJob : $returnedJob".trim()\n'
)
s = s.replace(
    '                    productState.text = "Fact Check · bridge indisponible"\n',
    '                    productState.text = "FACT CHECK O24 · BRIDGE INDISPONIBLE\\nJob : ${activeFactCheckJobId ?: \"—\"}"\n'
)

for token in [
    'FACT CHECK O24 · TRANSMIS',
    'État : PENDING_RESEARCH',
    'Recherche externe en attente',
    'Job : $returnedJob',
]:
    assert token in s, token
p.write_text(s)

(work / 'U013_BASELINE_LOCK.txt').write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_008\n'
    'INHERITED_RUNTIME=SHARED_007_O24_CAPTURE_PASS\n'
    'ANALYSE_RUNTIME=UNCHANGED_FROM_SHARED_006\n'
    'FACTCHECK_BRIDGE=O24_ANDROID_WEBAPP_V0.1\n'
    'FACTCHECK_OPERATION=capture\n'
    'FACTCHECK_VISIBLE_MODE_LABEL=FACT_CHECK_O24\n'
    'FACTCHECK_VISIBLE_JOB_ID=true\n'
    'FACTCHECK_VISIBLE_STATUS=PENDING_RESEARCH\n'
    'FACTCHECK_EXTERNAL_ORCHESTRATOR=NOT_YET_WIRED_FROM_ANDROID\n'
    'FACTCHECK_FINALIZE=NOT_AUTOMATIC\n'
    'CANONICAL_ENGINE_MODIFIED=false\n'
    'CANONICAL_GATEWAY_MODIFIED=false\n'
)
