from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()
subprocess.run([sys.executable, str(repo / 'u013ux008' / 'derive.py'), str(repo), str(work)], check=True)

p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared008"', 'applicationId = "nexus.android.u013.shared009"')
s = s.replace('versionCode = 53', 'versionCode = 54')
s = s.replace('versionName = "0.0.53-u013-android-ux-shared008-o24-visible-state"', 'versionName = "0.0.54-u013-android-ux-shared009-o24-dedicated-screen"')
assert 'nexus.android.u013.shared009' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

# Force a dedicated Fact Check result surface using the already-bound native resultSummary field.
old_start = '        productState.text = "FACT CHECK O24 · transmission…\\nJob : $jobId"\n'
new_start = '''        productHome.visibility = View.GONE
        resultPanel.visibility = View.VISIBLE
        webView.visibility = View.GONE
        productState.text = "FACT CHECK O24 · transmission…"
        resultSummary.text = "FACT CHECK O24\\n\\nAffirmation reçue\\n$rawClaim\\n\\nJob\\n$jobId\\n\\nÉtat\\nTRANSMISSION_O24"
'''
assert s.count(old_start) == 1
s = s.replace(old_start, new_start)

old_success = '''                        result == "ACCEPTED" && status == "PENDING_RESEARCH" && !engineCalled ->
                            "FACT CHECK O24 · TRANSMIS\\nJob : $returnedJob\\nÉtat : PENDING_RESEARCH\\nRecherche externe en attente"
'''
new_success = '''                        result == "ACCEPTED" && status == "PENDING_RESEARCH" && !engineCalled -> {
                            resultSummary.text = "FACT CHECK O24\\n\\nAffirmation reçue\\n$rawClaim\\n\\nJob\\n$returnedJob\\n\\nÉtat\\nPENDING_RESEARCH\\n\\nRecherche externe en attente\\n\\nMoteur\\nNON APPELÉ"
                            "FACT CHECK O24 · TRANSMIS"
                        }
'''
assert s.count(old_success) == 1
s = s.replace(old_success, new_success)

old_error = '                        errorCode.isNotBlank() -> "FACT CHECK O24 · $errorCode\\nJob : $returnedJob"\n'
new_error = '''                        errorCode.isNotBlank() -> {
                            resultSummary.text = "FACT CHECK O24\\n\\nAffirmation\\n$rawClaim\\n\\nJob\\n$returnedJob\\n\\nErreur\\n$errorCode"
                            "FACT CHECK O24 · $errorCode"
                        }
'''
assert s.count(old_error) == 1
s = s.replace(old_error, new_error)

old_else = '                        else -> "FACT CHECK O24 · $result $status\\nJob : $returnedJob".trim()\n'
new_else = '''                        else -> {
                            resultSummary.text = "FACT CHECK O24\\n\\nAffirmation\\n$rawClaim\\n\\nJob\\n$returnedJob\\n\\nRésultat bridge\\n$result $status"
                            "FACT CHECK O24 · $result $status".trim()
                        }
'''
assert s.count(old_else) == 1
s = s.replace(old_else, new_else)

old_catch = '                    productState.text = "FACT CHECK O24 · BRIDGE INDISPONIBLE\\nJob : ${activeFactCheckJobId ?: \"—\"}"\n'
new_catch = '''                    resultSummary.text = "FACT CHECK O24\\n\\nAffirmation\\n$rawClaim\\n\\nJob\\n${activeFactCheckJobId ?: "—"}\\n\\nÉtat\\nBRIDGE INDISPONIBLE"
                    productState.text = "FACT CHECK O24 · BRIDGE INDISPONIBLE"
'''
assert s.count(old_catch) == 1
s = s.replace(old_catch, new_catch)

for token in [
    'resultSummary.text = "FACT CHECK O24',
    'Affirmation reçue',
    'Recherche externe en attente',
    'Moteur\\nNON APPELÉ',
    'productHome.visibility = View.GONE',
    'resultPanel.visibility = View.VISIBLE',
]:
    assert token in s, token
p.write_text(s)

(work / 'U013_BASELINE_LOCK.txt').write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_009\n'
    'INHERITED_RUNTIME=SHARED_008_O24_VISIBLE_STATE\n'
    'ANALYSE_RUNTIME=UNCHANGED_FROM_SHARED_006\n'
    'FACTCHECK_BRIDGE=O24_ANDROID_WEBAPP_V0.1\n'
    'FACTCHECK_OPERATION=capture\n'
    'FACTCHECK_DEDICATED_RESULT_SCREEN=true\n'
    'FACTCHECK_RESULT_SURFACE=resultSummary\n'
    'FACTCHECK_VISIBLE_JOB_ID=true\n'
    'FACTCHECK_VISIBLE_STATUS=PENDING_RESEARCH\n'
    'FACTCHECK_VISIBLE_ENGINE_STATE=NOT_CALLED\n'
    'FACTCHECK_EXTERNAL_ORCHESTRATOR=NOT_YET_WIRED_FROM_ANDROID\n'
    'FACTCHECK_FINALIZE=NOT_AUTOMATIC\n'
    'CANONICAL_ENGINE_MODIFIED=false\n'
    'CANONICAL_GATEWAY_MODIFIED=false\n'
)
