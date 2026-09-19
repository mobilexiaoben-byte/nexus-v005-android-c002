from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start from product-first candidate 002.
subprocess.run([
    sys.executable,
    str(repo / 'u013ux002' / 'derive.py'),
    str(repo),
    str(work),
], check=True)

# Candidate identity.
p = work / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared002"', 'applicationId = "nexus.android.u013.shared003"')
s = s.replace('versionCode = 47', 'versionCode = 48')
s = s.replace('versionName = "0.0.47-u013-android-ux-shared002-product"', 'versionName = "0.0.48-u013-android-ux-shared003-native-result"')
assert 'nexus.android.u013.shared003' in s
p.write_text(s)

# Critical UX correction: NEVER expose provider WebView during normal Analyse flow.
p = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

old_analyse = '''        findViewById<Button>(R.id.productAnalyse).setOnClickListener {\n            productRunRequested = true\n            productState.text = "Analyse · résultat NEXUS"\n            productHome.visibility = View.GONE\n            if (resultPanel.visibility == View.VISIBLE) {\n                showNexusResult()\n            } else {\n                webView.visibility = View.VISIBLE\n            }\n        }\n'''
new_analyse = '''        findViewById<Button>(R.id.productAnalyse).setOnClickListener {\n            productRunRequested = true\n            productState.text = "Analyse en cours…"\n            webView.visibility = View.GONE\n            if (resultPanel.visibility == View.VISIBLE) {\n                showNexusResult()\n            } else {\n                productHome.visibility = View.VISIBLE\n            }\n        }\n'''
assert s.count(old_analyse) == 1, 'Analyse handler mismatch'
s = s.replace(old_analyse, new_analyse)

# Native result is the only normal terminal surface.
old_show = '''    private fun showNexusResult() {\n        webView.visibility = View.GONE\n        resultPanel.visibility = View.VISIBLE\n        if (productRunRequested) productHome.visibility = View.GONE\n    }\n'''
new_show = '''    private fun showNexusResult() {\n        webView.visibility = View.GONE\n        productHome.visibility = View.GONE\n        resultPanel.visibility = View.VISIBLE\n        productState.text = "Terminé · résultat validé"\n    }\n'''
assert s.count(old_show) == 1, 'showNexusResult mismatch'
s = s.replace(old_show, new_show)

# Provider page remains an explicit diagnostic/on-demand action only.
old_provider = '''    private fun showProviderResponse() {\n        resultPanel.visibility = View.GONE\n        webView.visibility = View.VISIBLE\n    }\n'''
new_provider = '''    private fun showProviderResponse() {\n        productHome.visibility = View.GONE\n        resultPanel.visibility = View.GONE\n        webView.visibility = View.VISIBLE\n    }\n'''
assert s.count(old_provider) == 1, 'showProviderResponse mismatch'
s = s.replace(old_provider, new_provider)

# Ensure automatic validation never leaves raw JSON as the normal terminal view.
old_validated = '''        if (productRunRequested) showNexusResult() else {\n            resultPanel.visibility = View.GONE\n            productHome.visibility = View.VISIBLE\n            productState.text = "Prêt · fournisseur disponible en arrière-plan"\n        }\n'''
new_validated = '''        webView.visibility = View.GONE\n        if (productRunRequested) {\n            showNexusResult()\n        } else {\n            resultPanel.visibility = View.GONE\n            productHome.visibility = View.VISIBLE\n            productState.text = "Prêt · fournisseur disponible en arrière-plan"\n        }\n'''
assert s.count(old_validated) == 1, 'validated transition mismatch'
s = s.replace(old_validated, new_validated)

# Static invariants for the corrected normal path.
assert 'productState.text = "Analyse en cours…"' in s
assert 'webView.visibility = View.GONE' in s
assert 'showValidatedResult(resultPack.optString("answer"), modelRef)' in s
assert 'private fun showValidatedResult(answer: String, modelRef: String?)' in s
p.write_text(s)

# Lock declares the normal UX guarantee; provider surface remains diagnostics-only.
lock = work / 'U013_BASELINE_LOCK.txt'
lock.write_text(
    'DESIGN_BASELINE_ID=BASELINE_UX_SHARED_001\n'
    'DESIGN_BASELINE_DRIVE=19cINcqyLSyoshqeRh-SeOlKoTaFoXFOrs31Hu--J54g\n'
    'RUNTIME_BASELINE=U004_ANDROID_UX_SHELL_004\n'
    'PLATFORM_ADAPTER=U013_ANDROID_UX_SHARED_003\n'
    'NON_MODIFIED_ORIGINALS=transport,auth,bridge,result_pack,fail_closed\n'
    'PRODUCT_HOME=IMPLEMENTED\n'
    'NORMAL_WAITING_SURFACE=NEXUS_NATIVE\n'
    'NORMAL_RESULT_SURFACE=NEXUS_NATIVE\n'
    'RESULT_RENDER_FIELD=result_pack.answer\n'
    'PROVIDER_WEBVIEW=NORMAL_FLOW_HIDDEN_DIAGNOSTICS_ONLY\n'
    'FACTCHECK_RUNTIME=NOT_CLAIMED\n'
)
