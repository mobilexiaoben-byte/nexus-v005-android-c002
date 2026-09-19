from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from candidate 003: native NEXUS waiting/result surfaces.
subprocess.run([
    sys.executable,
    str(repo / 'u013ux003' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Candidate identity.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared003"', 'applicationId = "nexus.android.u013.shared004"')
s = s.replace('versionCode = 48', 'versionCode = 49')
s = s.replace('versionName = "0.0.48-u013-android-ux-shared003-native-result"', 'versionName = "0.0.49-u013-android-ux-shared004-auth-state"')
assert 'nexus.android.u013.shared004' in s
p.write_text(s)

p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

# Analyse: if authentication is required, expose provider ONLY for login.
old_analyse = '''        findViewById<Button>(R.id.productAnalyse).setOnClickListener {
            productRunRequested = true
            productState.text = "Analyse en cours…"
            webView.visibility = View.GONE
            if (resultPanel.visibility == View.VISIBLE) {
                showNexusResult()
            } else {
                productHome.visibility = View.VISIBLE
            }
        }
'''
new_analyse = '''        findViewById<Button>(R.id.productAnalyse).setOnClickListener {
            productRunRequested = true
            if (currentHeadline.startsWith("AUTH REQUIRED")) {
                productState.text = "Connexion à ChatGPT requise"
                productHome.visibility = View.GONE
                resultPanel.visibility = View.GONE
                webView.visibility = View.VISIBLE
            } else {
                productState.text = "Analyse en cours…"
                webView.visibility = View.GONE
                if (resultPanel.visibility == View.VISIBLE) {
                    showNexusResult()
                } else {
                    productHome.visibility = View.VISIBLE
                }
            }
        }
'''
assert s.count(old_analyse) == 1, 'Analyse handler mismatch'
s = s.replace(old_analyse, new_analyse)

# Synchronize UX surface with the already-validated auth/runtime state machine.
old_render_tail = '''        status.text = buildString {
            append(friendlyHeadline(currentHeadline))
            if (diagnosticExpanded) {
                append("\\n").append(currentHeadline)
                diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT).forEach { event ->
                    append("\\n").append(event.line)
                    if (event.repeatCount > 1) append(" ×").append(event.repeatCount)
                }
                if (!currentBody.isNullOrBlank()) append("\\n").append(currentBody)
            }
        }
    }
'''
new_render_tail = '''        status.text = buildString {
            append(friendlyHeadline(currentHeadline))
            if (diagnosticExpanded) {
                append("\\n").append(currentHeadline)
                diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT).forEach { event ->
                    append("\\n").append(event.line)
                    if (event.repeatCount > 1) append(" ×").append(event.repeatCount)
                }
                if (!currentBody.isNullOrBlank()) append("\\n").append(currentBody)
            }
        }
        syncProductAuthSurface()
    }

    private fun syncProductAuthSurface() {
        if (!::productHome.isInitialized || !::productState.isInitialized) return

        when {
            currentHeadline.startsWith("AUTH REQUIRED") -> {
                if (productRunRequested) {
                    productState.text = "Connexion à ChatGPT requise"
                    productHome.visibility = View.GONE
                    resultPanel.visibility = View.GONE
                    webView.visibility = View.VISIBLE
                }
            }
            currentHeadline.startsWith("DESCRIBE PASS") ||
            currentHeadline.startsWith("ACK PASS") ||
            currentHeadline.startsWith("EXECUTION PROOF") -> {
                // Auth is proven: provider disappears automatically and NEXUS resumes.
                webView.visibility = View.GONE
                if (productRunRequested && !proofStopped) {
                    resultPanel.visibility = View.GONE
                    productHome.visibility = View.VISIBLE
                    productState.text = "Analyse en cours…"
                }
            }
        }
    }
'''
assert s.count(old_render_tail) == 1, 'renderStatus tail mismatch'
s = s.replace(old_render_tail, new_render_tail)

for token in [
    'currentHeadline.startsWith("AUTH REQUIRED")',
    'syncProductAuthSurface()',
    'Connexion à ChatGPT requise',
    'Auth is proven: provider disappears automatically and NEXUS resumes.',
    'webView.visibility = View.VISIBLE',
    'webView.visibility = View.GONE',
]:
    assert token in s, token
p.write_text(s)

lock = work / 'U013_BASELINE_LOCK.txt'
lock.write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'DESIGN_BASELINE_DRIVE=19cINcqyLSyoshqeRh-SeOlKoTaFoXFOrs31Hu--J54g\n'
    'RUNTIME_BASELINE=U004_ANDROID_UX_SHELL_004\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_004\n'
    'NON_MODIFIED_ORIGINALS=transport,auth_detection,bridge,result_pack,fail_closed\n'
    'AUTH_REQUIRED_SURFACE=PROVIDER_VISIBLE_FOR_LOGIN_ONLY\n'
    'AUTH_OK_RETURN=NEXUS_AUTOMATIC\n'
    'NORMAL_WAITING_SURFACE=NEXUS_NATIVE\n'
    'NORMAL_RESULT_SURFACE=NEXUS_NATIVE\n'
    'RESULT_RENDER_FIELD=result_pack.answer\n'
    'FACTCHECK_RUNTIME=NOT_CLAIMED\n'
)
