from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Start from the exact 008 candidate that was DEVICE-tested.
exec((repo / "reconcile008" / "provider_runtime_008.py").read_text(), {"__name__":"__main__", "__file__":str(repo / "reconcile008" / "provider_runtime_008.py"), "sys":sys})

main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main_path.read_text()

# Track the physical WebView origin separately from logical provider selection.
field_anchor = """    private var providerConfirmedByUser = false
    private val manualProviderConfirmationMode = true
"""
field_new = """    private var providerConfirmedByUser = false
    private var providerOriginConfirmed = false
    private var providerSwitchRetryCount = 0
    private val manualProviderConfirmationMode = true
"""
assert field_anchor in s, "provider state anchor missing"
s = s.replace(field_anchor, field_new, 1)

# Canonical origin helper used for switch/dispatch invariants.
helper_anchor = """    private fun isManualBrowserUrlAllowed(rawUrl: String): Boolean {
"""
helper = """    private fun canonicalOrigin(rawUrl: String): String {
        val uri = runCatching { Uri.parse(rawUrl) }.getOrNull() ?: return ""
        val scheme = uri.scheme?.lowercase() ?: return ""
        val host = uri.host?.lowercase() ?: return ""
        return "$scheme://$host"
    }

"""
assert helper_anchor in s, "manual browser helper anchor missing"
s = s.replace(helper_anchor, helper + helper_anchor, 1)

# A provider selection starts a real navigation transaction.
old = """    private fun selectProviderManually(provider: String, origin: String) {
        selectedProvider = provider
        selectedProviderOrigin = origin
        resetExecutionAttempt("PROVIDER_SWITCH:$provider")
        providerConfirmedByUser = false
        providerSelectionRequested = true
"""
new = """    private fun selectProviderManually(provider: String, origin: String) {
        selectedProvider = provider
        selectedProviderOrigin = origin
        resetExecutionAttempt("PROVIDER_SWITCH:$provider")
        providerConfirmedByUser = false
        providerOriginConfirmed = false
        providerSwitchRetryCount = 0
        providerSelectionRequested = true
"""
assert old in s, "provider switch anchor missing"
s = s.replace(old, new, 1)

# Page-finished is the authority for completing the physical provider switch.
old = """            override fun onPageFinished(view: WebView, url: String) {
                recordDiagnostic("onPageFinished", url, "main_frame=true")
            }
"""
new = """            override fun onPageFinished(view: WebView, url: String) {
                recordDiagnostic("onPageFinished", url, "main_frame=true")
                val expected = canonicalOrigin(selectedProviderOrigin ?: "")
                val actual = canonicalOrigin(url)
                if (providerSelectionRequested && !providerOriginConfirmed && expected.isNotBlank()) {
                    if (actual == expected) {
                        providerOriginConfirmed = true
                        providerSwitchRetryCount = 0
                        recordDiagnostic("PROVIDER_SWITCH_ORIGIN_CONFIRMED", url, "expected=$expected")
                    } else if (providerSwitchRetryCount < 2) {
                        providerSwitchRetryCount += 1
                        recordDiagnostic("PROVIDER_SWITCH_DESYNC_RETRY", url, "expected=$expected;actual=$actual;attempt=$providerSwitchRetryCount")
                        view.stopLoading()
                        handler.postDelayed({
                            if (providerSelectionRequested && !providerOriginConfirmed) {
                                view.loadUrl(selectedProviderOrigin ?: return@postDelayed)
                            }
                        }, 250L)
                    } else {
                        recordDiagnostic("PROVIDER_SWITCH_DESYNC", url, "expected=$expected;actual=$actual")
                        productState.text = "${selectedProvider ?: "LLM"} · changement de fournisseur non confirmé"
                    }
                }
            }
"""
assert old in s, "onPageFinished anchor missing"
s = s.replace(old, new, 1)

# "Connecté" is accepted only when the physical WebView is actually on the selected provider origin.
old = """        providerConfirmedByUser = true
        providerSelectionRequested = false
        lastProviderOrigin = (selectedProviderOrigin ?: "").trimEnd('/')
"""
new = """        val expectedOrigin = canonicalOrigin(selectedProviderOrigin ?: "")
        val actualOrigin = canonicalOrigin(webView.url ?: "")
        if (!providerOriginConfirmed || expectedOrigin.isBlank() || actualOrigin != expectedOrigin) {
            providerConfirmedByUser = false
            productState.text = "$provider · changement de fournisseur en cours"
            recordDiagnostic("PROVIDER_CONFIRMATION_REJECTED_ORIGIN_DESYNC", webView.url ?: "", "expected=$expectedOrigin;actual=$actualOrigin")
            return
        }
        providerConfirmedByUser = true
        providerSelectionRequested = false
        lastProviderOrigin = expectedOrigin
"""
assert old in s, "provider confirmation anchor missing"
s = s.replace(old, new, 1)

# Analyse is forbidden while logical and physical provider origins disagree.
old = """                val providerOrigin = selectedProviderOrigin?.trimEnd('/')
                if (!providerConfirmedByUser || providerOrigin.isNullOrBlank()) {
                    productState.text = "Confirmez d’abord la connexion du LLM via le menu ⋮"
                    return@setOnClickListener
                }
                lastProviderOrigin = providerOrigin
"""
new = """                val providerOrigin = selectedProviderOrigin?.trimEnd('/')
                val expectedOrigin = canonicalOrigin(providerOrigin ?: "")
                val actualOrigin = canonicalOrigin(webView.url ?: "")
                if (!providerConfirmedByUser || !providerOriginConfirmed || providerOrigin.isNullOrBlank() || expectedOrigin != actualOrigin) {
                    productState.text = "LLM non synchronisé · ouvrez le fournisseur puis confirmez la connexion"
                    recordDiagnostic("ANALYSE_PROVIDER_ORIGIN_GUARD", webView.url ?: "", "expected=$expectedOrigin;actual=$actualOrigin;confirmed=$providerConfirmedByUser")
                    return@setOnClickListener
                }
                lastProviderOrigin = expectedOrigin
"""
assert old in s, "Analyse provider gate anchor missing"
s = s.replace(old, new, 1)

# Replace the opaque one-shot bridge post failur by a bounded readiness wait.
old = """        if (bridge?.post(origin, outbound.toString()) != true) {
            block("ANDROID_EXECUTE_JOB_POST_FAILED")
            return
        }

        handler.postDelayed({
"""
new = """        postExecutionWhenBridgeReady(origin, outbound.toString(), 0)

        handler.postDelayed({
"""
assert old in s, "one-shot bridge post anchor missing"
s = s.replace(old, new, 1)

helper_anchor = """    private fun originForDiagnostics(): String =
"""
bridge_helper = """    private fun postExecutionWhenBridgeReady(origin: String, json: String, attempt: Int) {
        val activeBridge = bridge ?: run {
            block("ANDROID_EXECUTE_JOB_BRIDGE_UNAVAILABLE")
            return
        }
        val normalizedOrigin = canonicalOrigin(origin)
        if (canonicalOrigin(webView.url ?: "") != normalizedOrigin) {
            block("ANDROID_EXECUTE_JOB_ORIGIN_DESYNC")
            return
        }
        if (activeBridge.isReady(normalizedOrigin)) {
            val posted = runCatching { activeBridge.post(normalizedOrigin, json) }
                .getOrElse {
                    recordDiagnostic("EXECUTE_JOB_POST_EXCEPTION", normalizedOrigin, it.javaClass.simpleName + ":" + (it.message ?: ""))
                    false
                }
            if (!posted) block("ANDROID_EXECUTE_JOB_POST_REJECTED")
            else recordDiagnostic("EXECUTE_JOB_POSTED", normalizedOrigin, "bridge_ready=true;attempt=$attempt")
            return
        }
        if (attempt >= 15) {
            block("ANDROID_EXECUTE_JOB_BRIDGE_NOT_READY")
            return
        }
        recordDiagnostic("EXECUTE_JOB_WAIT_BRIDGE_READY", normalizedOrigin, "attempt=$attempt")
        handler.postDelayed({
            if (!proofStopped && !terminalReceived) {
                postExecutionWhenBridgeReady(normalizedOrigin, json, attempt + 1)
            }
        }, 300L)
    }

"""
assert helper_anchor in s, "originForDiagnostics anchor missing"
s = s.replace(helper_anchor, bridge_helper + helper_anchor, 1)

main_path.write_text(s)

# Expose bridge readiness.
bridge_path = root / "app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
b = bridge_path.read_text()
post_anchor = """    fun post(origin: String, json: String): Boolean {
"""
ready = """    fun isReady(origin: String): Boolean {
        if (!OriginPolicy.isBridgeOriginAllowed(origin)) return false
        return replyByOrigin.containsKey(origin)
    }

"""
assert post_anchor in b, "NexusWebBridge post anchor missing"
b = b.replace(post_anchor, ready + post_anchor, 1)
bridge_path.write_text(b)

# Every validated Android adapter emits a bridge-ready handshake at document start.
assets = root / "app/src/main/assets/nexus"
for name in ["chatgpt_provider_c002.js", "gemini_provider_c002.js", "zai_provider_c002.js"]:
    p = assets / name
    js = p.read_text()
    if "type:'BRIDGE_READY'" not in js:
        marker = "console.info("
        assert marker in js, f"console marker missing in {name}"
        js = js.replace(marker, "nativeSend({channel:CHANNEL,type:'BRIDGE_READY'}).catch(()=>{});\\n  " + marker, 1)
    p.write_text(js)

# Candidate identity.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 62" in g
assert 'versionName = "0.0.62-v007-m024-u013-provider-runtime008"' in g
g = g.replace("versionCode = 62", "versionCode = 63", 1)
g = g.replace(
    'versionName = "0.0.62-v007-m024-u013-provider-runtime008"',
    'versionName = "0.0.63-v007-m024-u013-provider-runtime009"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME009_SWITCH=LOGICAL_AND_PHYSICAL_ORIGIN_TRANSACTION\\n"
    "PROVIDER_RUNTIME009_CONNECTED_GUARD=WEBVIEW_ORIGIN_MATCH_REQUIRED\\n"
    "PROVIDER_RUNTIME009_ANALYSE_GUARD=WEBVIEW_ORIGIN_MATCH_REQUIRED\\n"
    "PROVIDER_RUNTIME009_BRIDGE_READY=EXPLICIT_HANDSHAKE_AND_BOUNDED_WAIT\\n"
    "PROVIDER_RUNTIME009_POST_FAILURE=DISCRIMINATED\\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\\n"
)

# Static invariants.
main = main_path.read_text()
bridge = bridge_path.read_text()
for token in [
    "PROVIDER_SWITCH_ORIGIN_CONFIRMED",
    "PROVIDER_SWITCH_DESYNC_RETRY",
    "PROVIDER_CONFIRMATION_REJECTED_ORIGIN_DESYNC",
    "ANALYSE_PROVIDER_ORIGIN_GUARD",
    "postExecutionWhenBridgeReady",
    "ANDROID_EXECUTE_JOB_BRIDGE_NOT_READY",
    "ANDROID_EXECUTE_JOB_ORIGIN_DESYNC",
    "ANDROID_EXECUTE_JOB_POST_REJECTED",
    "EXECUTE_JOB_POSTED",
]
for token in [
    "PROVIDER_SWITCH_ORIGIN_CONFIRMED",
    "PROVIDER_SWITCH_DESYNC_RETRY",
    "PROVIDER_CONFIRMATION_REJECTED_ORIGIN_DESYNC",
    "ANALYSE_PROVIDER_ORIGIN_GUARD",
    "postExecutionWhenBridgeReady",
    "ANDROID_EXECUTE_JOB_BRIDGE_NOT_READY",
    "ANDROID_EXECUTE_JOB_ORIGIN_DESYNC",
    "ANDROID_EXECUTE_JOB_POST_REJECTED",
    "EXECUTE_JOB_POSTED",
]:
    assert token in main, token
assert "ANDROID_EXECUTE_JOB_POST_FAILED" not in main
assert "fun isReady(origin: String): Boolean" in bridge
for name in ["chatgpt_provider_c002.js", "gemini_provider_c002.js", "zai_provider_c002.js"]:
    assert "type:'BRIDGE_READY'" in (assets / name).read_text(), name
