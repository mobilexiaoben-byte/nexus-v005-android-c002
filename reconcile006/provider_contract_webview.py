from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

subprocess.run([
    sys.executable,
    str(repo / 'reconcile005' / 'manual_provider_menu.py'),
    str(repo),
    str(root),
], check=True)

provider_dir = root / 'app/src/main/java/nexus/android/c002/provider'
provider_dir.mkdir(parents=True, exist_ok=True)
(provider_dir / 'ProviderContract.kt').write_text((repo / 'reconcile006' / 'ProviderContract.kt').read_text())

p = root / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = p.read_text()

def add_import(import_line):
    global s
    if import_line not in s:
        marker = 'import android.app.Activity\n'
        assert marker in s, marker
        s = s.replace(marker, marker + import_line + '\n', 1)

for imp in [
    'import android.app.AlertDialog',
    'import android.app.Dialog',
    'import android.content.Intent',
    'import android.webkit.CookieManager',
    'import android.widget.EditText',
    'import android.widget.LinearLayout',
    'import android.view.ViewGroup',
    'import nexus.android.c002.provider.ProviderCatalog',
]:
    add_import(imp)

field_anchor = '    private lateinit var productLlmChooser: Button\n'
field_new = '''    private lateinit var productLlmChooser: Button
    private val providerRegistry = linkedMapOf<String, String>()
'''
assert field_anchor in s, 'provider field anchor missing'
s = s.replace(field_anchor, field_new, 1)

bind_anchor = '        productLlmChooser.setOnClickListener { anchorView -> showLlmChooser(anchorView) }\n'
bind_new = bind_anchor + '        initializeProviderRegistry()\n'
assert bind_anchor in s, 'provider chooser bind anchor missing'
s = s.replace(bind_anchor, bind_new, 1)

start = s.index('    private fun showLlmChooser(anchorView: View) {')
end = s.index('    private fun selectProviderManually(provider: String, origin: String) {', start)
registry_methods = '''    private fun initializeProviderRegistry() {
        providerRegistry.clear()
        ProviderCatalog.builtIns.forEach { providerRegistry[it.displayName] = it.homeUrl }
        val prefs = getSharedPreferences("nexus_provider_registry_v1", MODE_PRIVATE)
        val raw = prefs.getString("custom_providers", null)
        if (!raw.isNullOrBlank()) {
            runCatching {
                val obj = JSONObject(raw)
                val keys = obj.keys()
                while (keys.hasNext()) {
                    val name = keys.next()
                    val url = obj.optString(name)
                    if (name.isNotBlank() && isValidProviderHome(url) && !providerRegistry.containsKey(name)) {
                        providerRegistry[name] = url
                    }
                }
            }
        }
    }

    private fun persistCustomProviders() {
        val builtInNames = ProviderCatalog.builtIns.map { it.displayName }.toSet()
        val obj = JSONObject()
        providerRegistry.forEach { (name, url) ->
            if (!builtInNames.contains(name)) obj.put(name, url)
        }
        getSharedPreferences("nexus_provider_registry_v1", MODE_PRIVATE)
            .edit()
            .putString("custom_providers", obj.toString())
            .apply()
    }

    private fun isValidProviderHome(raw: String): Boolean {
        val uri = runCatching { Uri.parse(raw) }.getOrNull() ?: return false
        return uri.scheme.equals("https", ignoreCase = true) && !uri.host.isNullOrBlank()
    }

    private fun showLlmChooser(anchorView: View) {
        val popup = PopupMenu(this, anchorView)
        providerRegistry.keys.forEach { popup.menu.add(it) }
        popup.menu.add("Ajouter un LLM…")
        popup.setOnMenuItemClickListener { item ->
            val label = item.title.toString()
            if (label == "Ajouter un LLM…") {
                showAddProviderDialog()
            } else {
                val origin = providerRegistry[label]
                if (origin != null) selectProviderManually(label, origin)
            }
            true
        }
        popup.show()
    }

    private fun showAddProviderDialog() {
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 24, 48, 0)
        }
        val nameInput = EditText(this).apply { hint = "Nom du LLM" }
        val urlInput = EditText(this).apply { hint = "https://…" }
        container.addView(nameInput)
        container.addView(urlInput)

        val dialog = AlertDialog.Builder(this)
            .setTitle("Ajouter un LLM")
            .setView(container)
            .setNegativeButton("Annuler", null)
            .setPositiveButton("Ajouter", null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val name = nameInput.text.toString().trim()
                val url = urlInput.text.toString().trim()
                when {
                    name.isBlank() -> nameInput.error = "Nom requis"
                    !isValidProviderHome(url) -> urlInput.error = "URL HTTPS valide requise"
                    ProviderCatalog.builtIns.any { it.displayName.equals(name, ignoreCase = true) } ->
                        nameInput.error = "Nom réservé"
                    else -> {
                        providerRegistry[name] = url
                        persistCustomProviders()
                        dialog.dismiss()
                        selectProviderManually(name, url)
                    }
                }
            }
        }
        dialog.show()
    }

'''
s = s[:start] + registry_methods + s[end:]

old_chrome = '''        webView.webChromeClient = object : WebChromeClient() {
            override fun onCreateWindow(
                view: WebView?,
                isDialog: Boolean,
                isUserGesture: Boolean,
                resultMsg: Message?
            ): Boolean {
                recordDiagnostic(
                    event = "onCreateWindow",
                    rawUrl = view?.url,
                    detail = "dialog=$isDialog;user_gesture=$isUserGesture"
                )
                block("EXECUTION_NEW_WINDOW_REQUESTED")
                return false
            }
        }
'''
new_chrome = '''        webView.webChromeClient = object : WebChromeClient() {
            override fun onCreateWindow(
                view: WebView?,
                isDialog: Boolean,
                isUserGesture: Boolean,
                resultMsg: Message?
            ): Boolean {
                recordDiagnostic(
                    event = "onCreateWindow",
                    rawUrl = view?.url,
                    detail = "dialog=$isDialog;user_gesture=$isUserGesture;manual_browser=true"
                )
                return createAuthPopup(resultMsg)
            }
        }
'''
assert old_chrome in s, 'WebChromeClient anchor missing'
s = s.replace(old_chrome, new_chrome, 1)

old_override = '''            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val rawUrl = request.url.toString()
                val allowed = OriginPolicy.isTopLevelNavigationAllowed(rawUrl)
                recordDiagnostic(
                    event = "shouldOverrideUrlLoading",
                    rawUrl = rawUrl,
                    detail = "main_frame=${request.isForMainFrame};allowed=$allowed"
                )
                return if (allowed) {
                    false
                } else {
                    block("ANDROID_NAVIGATION_ORIGIN_BLOCKED:${sanitizeHost(rawUrl)}")
                    true
                }
            }
'''
new_override = '''            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val rawUrl = request.url.toString()
                val manualAllowed = manualProviderConfirmationMode && request.isForMainFrame && isManualBrowserUrlAllowed(rawUrl)
                val policyAllowed = OriginPolicy.isTopLevelNavigationAllowed(rawUrl)
                val allowed = manualAllowed || policyAllowed
                recordDiagnostic(
                    event = "shouldOverrideUrlLoading",
                    rawUrl = rawUrl,
                    detail = "main_frame=${request.isForMainFrame};manual=$manualAllowed;policy=$policyAllowed;allowed=$allowed"
                )
                return when {
                    allowed -> false
                    handleExternalScheme(rawUrl) -> true
                    else -> {
                        recordDiagnostic("NAVIGATION_REJECTED", rawUrl, "unsupported_or_non_https")
                        true
                    }
                }
            }
'''
assert old_override in s, 'shouldOverrideUrlLoading anchor missing'
s = s.replace(old_override, new_override, 1)

old_err = '                if (request.isForMainFrame) block("EXECUTION_MAIN_FRAME_WEB_ERROR_${error.errorCode}")\n'
new_err = '                if (request.isForMainFrame && executionStarted && !terminalReceived) block("EXECUTION_MAIN_FRAME_WEB_ERROR_${error.errorCode}")\n'
assert old_err in s, 'web error anchor missing'
s = s.replace(old_err, new_err, 1)
old_http = '                if (request.isForMainFrame && statusCode >= 400) block("EXECUTION_MAIN_FRAME_HTTP_$statusCode")\n'
new_http = '                if (request.isForMainFrame && statusCode >= 400 && executionStarted && !terminalReceived) block("EXECUTION_MAIN_FRAME_HTTP_$statusCode")\n'
assert old_http in s, 'http error anchor missing'
s = s.replace(old_http, new_http, 1)

harden_anchor = '    private fun hardenWebView(view: WebView) {\n'
helpers = '''    private fun isManualBrowserUrlAllowed(rawUrl: String): Boolean {
        val uri = runCatching { Uri.parse(rawUrl) }.getOrNull() ?: return false
        val scheme = uri.scheme?.lowercase()
        return (scheme == "https" || scheme == "http") && !uri.host.isNullOrBlank()
    }

    private fun handleExternalScheme(rawUrl: String): Boolean {
        return runCatching {
            val intent = if (rawUrl.startsWith("intent:", ignoreCase = true)) {
                Intent.parseUri(rawUrl, Intent.URI_INTENT_SCHEME)
            } else {
                Intent(Intent.ACTION_VIEW, Uri.parse(rawUrl))
            }
            startActivity(intent)
            recordDiagnostic("EXTERNAL_NAVIGATION", rawUrl, "delegated_to_android")
            true
        }.getOrDefault(false)
    }

    private fun createAuthPopup(resultMsg: Message?): Boolean {
        val transport = resultMsg?.obj as? WebView.WebViewTransport ?: return false
        val dialog = Dialog(this)
        val popup = WebView(this)

        if (WebViewFeature.isFeatureSupported(WebViewFeature.MULTI_PROFILE)) {
            runCatching { WebViewCompat.setProfile(popup, PROFILE_NAME) }
        }
        hardenWebView(popup)

        popup.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val rawUrl = request.url.toString()
                val allowed = isManualBrowserUrlAllowed(rawUrl)
                recordDiagnostic("popupNavigation", rawUrl, "allowed=$allowed")
                return if (allowed) false else handleExternalScheme(rawUrl)
            }

            override fun onPageFinished(view: WebView, url: String) {
                recordDiagnostic("popupPageFinished", url, "auth_popup=true")
            }
        }
        popup.webChromeClient = object : WebChromeClient() {
            override fun onCloseWindow(window: WebView?) {
                runCatching { dialog.dismiss() }
            }
        }

        dialog.setOnDismissListener {
            runCatching { popup.stopLoading() }
            runCatching { popup.destroy() }
            selectedProviderOrigin?.let { origin ->
                webView.visibility = View.VISIBLE
                webView.loadUrl(origin)
            }
        }
        dialog.setContentView(
            popup,
            ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        )
        transport.webView = popup
        resultMsg.sendToTarget()
        dialog.show()
        dialog.window?.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        return true
    }

'''
assert harden_anchor in s, 'hardenWebView anchor missing'
s = s.replace(harden_anchor, helpers + harden_anchor, 1)

old_harden = '''    private fun hardenWebView(view: WebView) {
        with(view.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            setSupportMultipleWindows(true)
            javaScriptCanOpenWindowsAutomatically = false
        }
        WebView.setWebContentsDebuggingEnabled(false)
    }
'''
new_harden = '''    private fun hardenWebView(view: WebView) {
        with(view.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            setSupportMultipleWindows(true)
            javaScriptCanOpenWindowsAutomatically = true
        }
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(view, true)
        WebView.setWebContentsDebuggingEnabled(false)
    }
'''
assert old_harden in s, 'hardenWebView body missing'
s = s.replace(old_harden, new_harden, 1)

p.write_text(s)

p = root / 'app/build.gradle.kts'
s = p.read_text()
s = s.replace('applicationId = "nexus.android.v007.m024.u013.manualprovider005"', 'applicationId = "nexus.android.v007.m024.u013.providercontract006"')
s = s.replace('versionCode = 59', 'versionCode = 60')
s = s.replace('versionName = "0.0.59-v007-m024-u013-manual-provider-menu005"', 'versionName = "0.0.60-v007-m024-u013-provider-contract-webview006"')
assert 'nexus.android.v007.m024.u013.providercontract006' in s
p.write_text(s)

lock = root / 'RECONCILIATION_LOCK.txt'
base = lock.read_text()
lock.write_text(base +
    'PROVIDER_CONTRACT=V1_STANDARD_REQUEST_RESULT\\n'
    'PROVIDER_CATALOG=ChatGPT,Gemini,Claude,Z.ai,Grok,DeepSeek\\n'
    'CUSTOM_PROVIDER_REGISTRY=PERSISTED_NAVIGATION_ONLY\\n'
    'CUSTOM_PROVIDER_EXECUTION=NOT_CLAIMED_WITHOUT_ADAPTER\\n'
    'MANUAL_WEBVIEW_NAVIGATION=HTTPS_TOP_LEVEL_ALLOWED\\n'
    'OAUTH_POPUP_SUPPORT=WEBCHROME_CHILD_WEBVIEW_SHARED_PROFILE\\n'
    'THIRD_PARTY_COOKIES=ENABLED_FOR_PROVIDER_LOGIN\\n'
    'DOM_AUTH_INFERENCE=NOT_PRODUCT_AUTHORITY\\n'
    'BRIDGE_ORIGIN_RESTRICTIONS=PRESERVED\\n'
)

main = (root / 'app/src/main/java/nexus/android/c002/MainActivity.kt').read_text()
contract = (root / 'app/src/main/java/nexus/android/c002/provider/ProviderContract.kt').read_text()
for token in [
    'ProviderCatalog.builtIns',
    'Ajouter un LLM…',
    'showAddProviderDialog()',
    'persistCustomProviders()',
    'createAuthPopup(resultMsg)',
    'CookieManager.getInstance().setAcceptThirdPartyCookies(view, true)',
    'javaScriptCanOpenWindowsAutomatically = true',
    'manualProviderConfirmationMode && request.isForMainFrame && isManualBrowserUrlAllowed(rawUrl)',
    'executionStarted && !terminalReceived',
]:
    assert token in main, token
for token in [
    'ProviderManifest("deepseek", "DeepSeek", "https://chat.deepseek.com/"',
    'interface ProviderAdapter',
    'data class ProviderRequest',
    'data class ProviderResult',
]:
    assert token in contract, token
