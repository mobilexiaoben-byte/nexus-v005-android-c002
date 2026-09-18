from pathlib import Path
import shutil
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Start from current V007 provider contract/WebView 006.
subprocess.run([
    sys.executable,
    str(repo / "reconcile006" / "provider_contract_webview.py"),
    str(repo),
    str(root),
], check=True)

# Restore the validated Z.ai Android provider adapter lineage as a delta only.
assets = root / "app/src/main/assets/nexus"
shutil.copy2(repo / "reconcile007" / "zai_provider_c002.js", assets / "zai_provider_c002.js")

# Transport contract: only DEVICE-proven Android adapters are enabled here.
p = root / "app/src/main/java/nexus/android/c002/core/TransportContract.kt"
s = p.read_text()
s = s.replace(
    "enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI }",
    "enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI, ZAI }"
)
anchor = '        SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true)\n'
assert anchor in s, "Gemini policy anchor missing"
s = s.replace(
    anchor,
    anchor.rstrip("\n") + ',\n        SelectedProvider.ZAI to ProviderPolicy("ZAI", "ADP-ZAI-GLM-FAMILY", "https://chat.z.ai", true)\n'
)
p.write_text(s)

# Z.ai is an isolated execution-bridge origin, not a blanket navigation authority.
p = root / "app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
s = p.read_text()
anchor = '        "https://gemini.google.com"\n'
assert anchor in s, "Gemini bridge origin anchor missing"
s = s.replace(anchor, '        "https://gemini.google.com",\n        "https://chat.z.ai"\n', 1)
p.write_text(s)

# Install the Z.ai adapter in the same isolated bridge world.
p = root / "app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
s = p.read_text()
old = "fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String): BridgeInstallResult {"
new = "fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String, zaiAdapterScript: String): BridgeInstallResult {"
assert old in s, "bridge install signature 006 missing"
s = s.replace(old, new, 1)
anchor = '''        WebViewCompat.addJavaScriptOnEvent(
            webView,
            geminiAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://gemini.google.com"),
            isolatedWorld
        )
        return BridgeInstallResult(true, "PASS")
'''
insert = '''        WebViewCompat.addJavaScriptOnEvent(
            webView,
            geminiAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://gemini.google.com"),
            isolatedWorld
        )
        WebViewCompat.addJavaScriptOnEvent(
            webView,
            zaiAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://chat.z.ai"),
            isolatedWorld
        )
        return BridgeInstallResult(true, "PASS")
'''
assert anchor in s, "Gemini injection anchor missing"
s = s.replace(anchor, insert, 1)
p.write_text(s)

p = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = p.read_text()

# Load/install the Z.ai adapter.
old = '''        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter)
'''
new = '''        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }
        val zaiAdapter = assets.open("nexus/zai_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter, zaiAdapter)
'''
assert old in s, "adapter install call missing"
s = s.replace(old, new, 1)

# Manual connection confirmation authorizes dispatch; the provider adapter still
# performs its own live session check and fails closed if the session is unusable.
old = '''        providerConfirmedByUser = true
        providerSelectionRequested = false
        webView.visibility = View.GONE
'''
new = '''        providerConfirmedByUser = true
        providerSelectionRequested = false
        lastProviderOrigin = (selectedProviderOrigin ?: "").trimEnd('/')
        webView.visibility = View.GONE
'''
assert old in s, "manual confirmation anchor missing"
s = s.replace(old, new, 1)

# Fix the deadlock observed on device: manual-confirmation mode intentionally
# bypasses DOM-derived DESCRIBE product state, so Analyse must not require
# describePassed before dispatch.
old = '''                val providerOrigin = lastProviderOrigin
                if (!describePassed || providerOrigin.isNullOrBlank()) {
                    productState.text = "Connexion au LLM en cours…"
                    return@setOnClickListener
                }
                productState.text = "Analyse en cours…"
                resultPanel.visibility = View.GONE
                webView.visibility = View.GONE
                productHome.visibility = View.VISIBLE
                startExecutionProof(providerOrigin)
'''
new = '''                val providerOrigin = selectedProviderOrigin?.trimEnd('/')
                if (!providerConfirmedByUser || providerOrigin.isNullOrBlank()) {
                    productState.text = "Confirmez d’abord la connexion du LLM via le menu ⋮"
                    return@setOnClickListener
                }
                lastProviderOrigin = providerOrigin
                productState.text = "Analyse en cours…"
                resultPanel.visibility = View.GONE
                webView.visibility = View.GONE
                productHome.visibility = View.VISIBLE
                startExecutionProof(providerOrigin)
'''
assert old in s, "Analyse dispatch gate anchor missing"
s = s.replace(old, new, 1)

# Accept only the three Android provider channels with DEVICE-PASS lineage.
old = 'if (message.optString("channel") != CHATGPT_CHANNEL && message.optString("channel") != GEMINI_CHANNEL) return'
new = 'if (message.optString("channel") != CHATGPT_CHANNEL && message.optString("channel") != GEMINI_CHANNEL && message.optString("channel") != ZAI_CHANNEL) return'
assert old in s, "bridge channel gate anchor missing"
s = s.replace(old, new, 1)

# Dispatch through the selected validated adapter instead of always ChatGPT.
anchor = '''    private fun startExecutionProof(origin: String) {
        if (!describePassed || executionStarted || proofStopped) return
        val userQuestion = activeUserQuestion?.trim().orEmpty()
'''
replacement = '''    private fun startExecutionProof(origin: String) {
        if (executionStarted || proofStopped) return
        val provider = when (selectedProvider) {
            "ChatGPT" -> SelectedProvider.CHATGPT
            "Gemini" -> SelectedProvider.GEMINI
            "Z.ai" -> SelectedProvider.ZAI
            "Claude" -> {
                productState.text = "Claude · limitation Android non certifiée"
                return
            }
            else -> {
                productState.text = "${selectedProvider ?: "LLM"} · adaptateur d’exécution Android non validé"
                return
            }
        }
        val executionChannel = when (provider) {
            SelectedProvider.CHATGPT -> CHATGPT_CHANNEL
            SelectedProvider.GEMINI -> GEMINI_CHANNEL
            SelectedProvider.ZAI -> ZAI_CHANNEL
            else -> CHATGPT_CHANNEL
        }
        val expectedProviderLabel = when (provider) {
            SelectedProvider.CHATGPT -> "OpenAI"
            SelectedProvider.GEMINI -> "Google"
            SelectedProvider.ZAI -> "Z.ai"
            else -> ""
        }
        val userQuestion = activeUserQuestion?.trim().orEmpty()
'''
assert anchor in s, "startExecutionProof anchor missing"
s = s.replace(anchor, replacement, 1)
s = s.replace('            provider = SelectedProvider.CHATGPT,', '            provider = provider,', 1)
s = s.replace('.put("provider", "OpenAI")', '.put("provider", expectedProviderLabel)', 1)
s = s.replace('.put("channel", CHATGPT_CHANNEL)', '.put("channel", executionChannel)', 1)

# M024 policy must be carried as the actual provider envelope field.
policy_anchor = '.put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")'
assert policy_anchor in s, "M024 policy contract marker missing"
s = s.replace(policy_anchor, policy_anchor + '\n            .put("research_policy", job.researchPolicy.name)', 1)

# Provider-specific provenance, UI-origin and visible labels.
s = s.replace('recordDiagnostic("ACK_PASS", CHATGPT_ORIGIN, "bridge_run_id=$BRIDGE_RUN_ID")',
              'recordDiagnostic("ACK_PASS", proofJob?.origin ?: originForDiagnostics(), "bridge_run_id=$BRIDGE_RUN_ID")', 1)
s = s.replace('currentHeadline = "ACK PASS — provider polling ChatGPT UI"',
              'currentHeadline = "ACK PASS — provider polling ${selectedProvider ?: "LLM"} UI"', 1)
s = s.replace('recordDiagnostic("PROVIDER_PROGRESS", CHATGPT_ORIGIN, "status=$jobStatus")',
              'recordDiagnostic("PROVIDER_PROGRESS", proofJob?.origin ?: originForDiagnostics(), "status=$jobStatus")', 1)

# Add a small helper used by provider-agnostic diagnostics.
helper_anchor = '    private fun handleProviderAck(message: JSONObject) {\n'
assert helper_anchor in s, "ACK method anchor missing"
s = s.replace(helper_anchor, '''    private fun originForDiagnostics(): String =
        proofJob?.origin ?: lastProviderOrigin ?: selectedProviderOrigin?.trimEnd('/') ?: ""

''' + helper_anchor, 1)

# Validate dynamic provider/model provenance rather than hard-coded OpenAI.
old = '''        if (model.optString("provider") != "OpenAI") return "ANDROID_RESULT_PROVIDER_MODEL_MISMATCH"
        if (model.optString("model") != MODEL_REF) return "ANDROID_RESULT_MODEL_REF_MISMATCH"
'''
new = '''        val expectedProvider = when (job.providerFamily) {
            "OPENAI" -> "OpenAI"
            "GOOGLE" -> "Google"
            "ZAI" -> "Z.ai"
            else -> return "ANDROID_RESULT_PROVIDER_FAMILY_UNSUPPORTED"
        }
        if (model.optString("provider") != expectedProvider) return "ANDROID_RESULT_PROVIDER_MODEL_MISMATCH"
        if (model.optString("model").isBlank()) return "ANDROID_RESULT_MODEL_REF_MISSING"
'''
assert old in s, "hard-coded provider validation anchor missing"
s = s.replace(old, new, 1)

old = '''        if (uiOrigin != CHATGPT_ORIGIN) {
            block("ANDROID_PROVIDER_UI_ORIGIN_MISMATCH")
            return
        }
'''
new = '''        if (uiOrigin != job.origin.trimEnd('/')) {
            block("ANDROID_PROVIDER_UI_ORIGIN_MISMATCH")
            return
        }
'''
assert old in s, "hard-coded UI origin anchor missing"
s = s.replace(old, new, 1)

# Fact Check: remove the token dialog from the user journey. Credential remains
# internal and is reused from the existing app-private store on upgrade.
s = s.replace('            ensureO24TokenThenCapture(rawClaim)', '            startO24CaptureUsingInternalCredential(rawClaim)', 1)
start = s.index('    private fun ensureO24TokenThenCapture(rawClaim: String) {')
end = s.index('    private fun startO24Capture(rawClaim: String, token: String) {', start)
internal_method = '''    private fun startO24CaptureUsingInternalCredential(rawClaim: String) {
        val prefs = getSharedPreferences(O24_PREFS, MODE_PRIVATE)
        val token = prefs.getString(O24_TOKEN_KEY, "").orEmpty().trim()
        if (token.isBlank()) {
            productState.text = "Fact Check · autorisation interne indisponible"
            recordDiagnostic("O24_INTERNAL_CREDENTIAL_MISSING", O24_BRIDGE_URL, "NO_USER_TOKEN_PROMPT")
            return
        }
        startO24Capture(rawClaim, token)
    }

'''
s = s[:start] + internal_method + s[end:]

# Add Z.ai execution constants.
const_anchor = '        const val GEMINI_CHANNEL = "NEXUS_V007_GEMINI_DIAG_004"\n'
assert const_anchor in s, "Gemini channel constant missing"
s = s.replace(const_anchor, const_anchor + '        const val ZAI_CHANNEL = "NEXUS_V005_ZAI_001"\n', 1)

# Claude remains visible/navigation-capable but not execution-certified on Android.
assert '"Claude" -> {' in s

p.write_text(s)

# Keep the same applicationId to preserve app-private provider and Fact Check
# credential state across the 006 -> 007 upgrade.
p = root / "app/build.gradle.kts"
s = p.read_text()
assert 'applicationId = "nexus.android.v007.m024.u013.providercontract006"' in s
s = s.replace('versionCode = 60', 'versionCode = 61', 1)
s = s.replace(
    'versionName = "0.0.60-v007-m024-u013-provider-contract-webview006"',
    'versionName = "0.0.61-v007-m024-u013-execution-tokenless007"',
    1
)
p.write_text(s)

# Product-oriented prompt semantics for Gemini; Z.ai file above already uses them.
p = assets / "gemini_provider_c002.js"
s = p.read_text()
s = s.replace('You are executing a NEXUS read-only post-response audit in this authenticated Gemini browser session.',
              'You are executing a NEXUS read-only user analysis in this authenticated Gemini browser session.')
s = s.replace('- Use only the supplied frozen package below.',
              '- Answer the QUESTION directly using your current model knowledge and the supplied frozen package metadata.')
s = s.replace('- Do NOT rewrite Analysis A.',
              '- Keep the answer concise, useful, and directly responsive to QUESTION.')
s = s.replace('- Return exactly frozen_package.output_contract.expected_result_pack as the JSON response.',
              '- Preserve the expected Result Pack structure and static fields, but replace expected_result_pack.answer with your substantive answer to QUESTION.')
p.write_text(s)

# Lock and build-time assertions.
lock = root / "RECONCILIATION_LOCK.txt"
base = lock.read_text()
lock.write_text(base +
    'EXECUTION007_ANALYSE_DEADLOCK_FIX=MANUAL_CONFIRMATION_DISPATCH\n'
    'EXECUTION007_VALIDATED_ANDROID_ADAPTERS=CHATGPT,GEMINI,ZAI\n'
    'EXECUTION007_CLAUDE=LIMITATION_ANDROID_NON_CERTIFIED\n'
    'EXECUTION007_GROK_DEEPSEEK=NAVIGATION_ONLY_NO_VALIDATED_ANDROID_ADAPTER\n'
    'EXECUTION007_M024_POLICY_FIELD=research_policy\n'
    'FACTCHECK_TOKEN_UI=REMOVED\n'
    'FACTCHECK_CREDENTIAL=APP_PRIVATE_INTERNAL_REUSE_FAIL_CLOSED_IF_MISSING\n'
    'APPLICATION_ID_STABLE_FROM_006=true\n'
    'DEVICE_PASS=NOT_YET_ACQUIRED\n'
)

main = (root / "app/src/main/java/nexus/android/c002/MainActivity.kt").read_text()
for token in [
    'providerConfirmedByUser || providerOrigin.isNullOrBlank()',
    'SelectedProvider.ZAI',
    'ZAI_CHANNEL',
    '.put("research_policy", job.researchPolicy.name)',
    'startO24CaptureUsingInternalCredential(rawClaim)',
    'NO_USER_TOKEN_PROMPT',
    'Claude · limitation Android non certifiée',
]:
    assert token in main, token
assert 'ensureO24TokenThenCapture(rawClaim)' not in main
assert 'AlertDialog.Builder(this)\n            .setTitle("Connexion Fact Check O24")' not in main
assert 'versionCode = 61' in (root / "app/build.gradle.kts").read_text()
