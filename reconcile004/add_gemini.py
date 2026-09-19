from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1]).resolve()
repo = Path(sys.argv[2]).resolve()

# Add the historically DEVICE-PASS Gemini adapter, updated for M-024 policy transport.
assets = root / "app/src/main/assets/nexus"
shutil.copy2(repo / "reconcile004/gemini_provider_c002.js", assets / "gemini_provider_c002.js")

# Enable the already-declared Gemini provider policy.
p = root / "app/src/main/java/nexus/android/c002/core/TransportContract.kt"
s = p.read_text()
old = 'SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", false)'
new = 'SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true)'
assert old in s, "Gemini disabled policy anchor missing"
s = s.replace(old, new)
p.write_text(s)

# The baseline core suite intentionally expected Gemini disabled. This diagnostic candidate
# explicitly enables Gemini, so invert only that named expectation while preserving all other gates.
test = root / "core-tests/TestMain.kt"
ts = test.read_text()
lines = ts.splitlines()
changed = False
for i, line in enumerate(lines):
    if 'T24 Gemini disabled' in line:
        nl = line.replace('"T24 Gemini disabled"', '"T24 Gemini enabled diagnostic"')
        if ', !' in nl:
            nl = nl.replace(', !', ', ', 1)
        elif ',!' in nl:
            nl = nl.replace(',!', ',', 1)
        elif '== false' in nl:
            nl = nl.replace('== false', '== true', 1)
        elif 'runCatching' in nl and '.isFailure' in nl:
            nl = nl.replace('.isFailure', '.isSuccess', 1)
        else:
            raise AssertionError('Unsupported T24 Gemini disabled expression: ' + line)
        lines[i] = nl
        changed = True
        break
assert changed, 'T24 Gemini disabled test anchor missing'
test.write_text('\n'.join(lines) + '\n')

# Allow Gemini as an isolated bridge origin and bounded top-level navigation origin.
p = root / "app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
s = p.read_text()
old = '''        "https://chatgpt.com",
        "https://claude.ai"
'''
new = '''        "https://chatgpt.com",
        "https://claude.ai",
        "https://gemini.google.com"
'''
assert old in s, "bridgeOrigins anchor missing"
s = s.replace(old, new)
old = '''            host == "claude.ai" || host.endsWith(".claude.ai") ||
            host == "anthropic.com" || host.endsWith(".anthropic.com") ||
'''
new = '''            host == "claude.ai" || host.endsWith(".claude.ai") ||
            host == "anthropic.com" || host.endsWith(".anthropic.com") ||
            host == "gemini.google.com" || host.endsWith(".gemini.google.com") ||
'''
assert old in s, "Gemini navigation host anchor missing"
s = s.replace(old, new)
p.write_text(s)

# Install Gemini in the same isolated bridge world as ChatGPT and Claude.
p = root / "app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
s = p.read_text()
old = 'fun install(chatGptAdapterScript: String, claudeAdapterScript: String): BridgeInstallResult {'
new = 'fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String): BridgeInstallResult {'
assert old in s, "bridge install signature anchor missing"
s = s.replace(old, new)
old = '''        WebViewCompat.addJavaScriptOnEvent(
            webView,
            claudeAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://claude.ai"),
            isolatedWorld
        )
        return BridgeInstallResult(true, "PASS")
'''
new = '''        WebViewCompat.addJavaScriptOnEvent(
            webView,
            claudeAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://claude.ai"),
            isolatedWorld
        )
        WebViewCompat.addJavaScriptOnEvent(
            webView,
            geminiAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://gemini.google.com"),
            isolatedWorld
        )
        return BridgeInstallResult(true, "PASS")
'''
assert old in s, "Claude bridge injection anchor missing"
s = s.replace(old, new)
p.write_text(s)

# Extend the U-013 product chooser with a real Gemini diagnostic route.
p = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = p.read_text()

old = '''        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }
        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter)
'''
new = '''        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }
        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }
        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter)
'''
assert old in s, "MainActivity bridge install anchor missing"
s = s.replace(old, new)

s = s.replace('popup.menu.add("Gemini · adaptateur Android à raccorder")', 'popup.menu.add("Gemini")')
old = '''            when (item.title.toString()) {
                "ChatGPT" -> selectChatGptProvider()
                else -> productState.text = item.title.toString()
            }
'''
new = '''            when (item.title.toString()) {
                "ChatGPT" -> selectChatGptProvider()
                "Gemini" -> selectGeminiProvider()
                else -> productState.text = item.title.toString()
            }
'''
assert old in s, "LLM chooser routing anchor missing"
s = s.replace(old, new)

anchor = '''    private fun syncProductAuthSurface() {
'''
gemini_method = '''    private fun selectGeminiProvider() {
        selectedProvider = "Gemini"
        productLlmChooser.text = "LLM · Gemini"
        productRunRequested = false
        providerSelectionRequested = true
        describePassed = false
        productState.text = "Connexion à Gemini…"
        productHome.visibility = View.GONE
        resultPanel.visibility = View.GONE
        webView.visibility = View.VISIBLE
        webView.stopLoading()
        webView.loadUrl(GEMINI_ORIGIN + "/")
        recordDiagnostic("PROVIDER_NAVIGATION", GEMINI_ORIGIN, "GEMINI_EXPLICIT_LOAD_DIAGNOSTIC")
    }

    private fun handleGeminiStatus(origin: String, message: JSONObject) {
        if (origin != GEMINI_ORIGIN) return
        val status = message.optJSONObject("status") ?: return
        val state = status.optString("state")
        val reason = status.optString("reason")
        recordDiagnostic("GEMINI_STATUS", origin, state + ":" + reason)
        if (selectedProvider != "Gemini") return
        when (state) {
            "AUTHENTICATED" -> {
                describePassed = true
                providerSelectionRequested = false
                webView.visibility = View.GONE
                resultPanel.visibility = View.GONE
                productHome.visibility = View.VISIBLE
                productLlmChooser.text = "LLM · Gemini"
                productState.text = "Gemini connecté · prêt"
            }
            "GUEST_READY" -> {
                describePassed = false
                providerSelectionRequested = false
                webView.visibility = View.GONE
                resultPanel.visibility = View.GONE
                productHome.visibility = View.VISIBLE
                productLlmChooser.text = "LLM · Gemini"
                productState.text = "Gemini disponible · mode invité"
            }
            "UNAUTHENTICATED" -> {
                describePassed = false
                providerSelectionRequested = true
                productState.text = "Connexion à Gemini requise"
                productHome.visibility = View.GONE
                resultPanel.visibility = View.GONE
                webView.visibility = View.VISIBLE
            }
        }
    }

'''
assert anchor in s, "syncProductAuthSurface anchor missing"
s = s.replace(anchor, gemini_method + anchor, 1)

# Accept both provider channels, but keep existing ChatGPT execution routing untouched.
old = 'if (message.optString("channel") != CHATGPT_CHANNEL) return'
new = 'if (message.optString("channel") != CHATGPT_CHANNEL && message.optString("channel") != GEMINI_CHANNEL) return'
if old in s:
    s = s.replace(old, new)

old = '"CHATGPT_STATUS" -> handleStatus(origin, message)'
new = '"CHATGPT_STATUS" -> handleStatus(origin, message)\n            "GEMINI_STATUS" -> handleGeminiStatus(origin, message)'
assert old in s, "CHATGPT_STATUS routing anchor missing"
s = s.replace(old, new)

# Add bounded Gemini constants without changing the existing ChatGPT execution constants.
const_anchor = 'const val CHATGPT_ORIGIN = "https://chatgpt.com"'
assert const_anchor in s, "CHATGPT_ORIGIN constant missing"
s = s.replace(const_anchor, const_anchor + '\n        const val GEMINI_ORIGIN = "https://gemini.google.com"')
channel_anchor = 'const val CHATGPT_CHANNEL = "NEXUS_POC022_C8B2R1"'
assert channel_anchor in s, "CHATGPT_CHANNEL constant missing"
s = s.replace(channel_anchor, channel_anchor + '\n        const val GEMINI_CHANNEL = "NEXUS_V007_GEMINI_DIAG_004"')

for token in [
    'popup.menu.add("Gemini")',
    '"Gemini" -> selectGeminiProvider()',
    'webView.loadUrl(GEMINI_ORIGIN + "/")',
    '"GEMINI_STATUS" -> handleGeminiStatus(origin, message)',
    'Gemini connecté · prêt',
    'Gemini disponible · mode invité',
    '"GUEST_READY" -> {',
    'GEMINI_EXPLICIT_LOAD_DIAGNOSTIC',
]:
    assert token in s, token
p.write_text(s)

# Unique candidate identity, preserving RECONCILE-002 lineage and no promotion.
p = root / "app/build.gradle.kts"
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.m024.u013.reconcile002"', 'applicationId = "nexus.android.v007.m024.u013.reconcile004gemini"')
s = s.replace('versionCode = 56', 'versionCode = 58')
s = s.replace('versionName = "0.0.56-v007-m024-u013-authfix2-reconcile002"', 'versionName = "0.0.58-v007-m024-u013-authfix2-reconcile004-gemini"')
assert 'nexus.android.v007.m024.u013.reconcile004gemini' in s
p.write_text(s)

lock = root / "RECONCILIATION_LOCK.txt"
base = lock.read_text()
lock.write_text(base +
    'SECOND_PROVIDER_DIAGNOSTIC=GEMINI\n'
    'GEMINI_ADAPTER=HISTORICAL_DEVICE_PASS_LINEAGE_V004_UPDATED_FOR_M024\n'
    'GEMINI_D02_SCOPE=OPEN_NAVIGATION_AUTH_STATUS_GUEST_READY_RETURN\n'
    'GEMINI_FULL_ANALYSIS_EXECUTION=NOT_CLAIMED_BY_THIS_DIAGNOSTIC\nGEMINI_GUEST_READY=VISIBLE_COMPOSER_USABLE_WITHOUT_ACCOUNT_AUTH\n'
)
