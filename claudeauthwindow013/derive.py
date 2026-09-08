from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Rebuild strictly from AUTH STABILITY 012. Provider assets and OriginPolicy stay byte-identical.
subprocess.run([
    'python3', str(repo / 'claudeauthstability012' / 'derive.py'), str(repo), str(work)
], check=True)

p = work / 'app/build.gradle.kts'
g = p.read_text()
for before, after in [
    ('applicationId = "nexus.android.c002.claudeauthstability012"', 'applicationId = "nexus.android.c002.claudeauthwindow013"'),
    ('versionCode = 13', 'versionCode = 14'),
    ('versionName = "0.0.13-c002-claude-authstability012"', 'versionName = "0.0.14-c002-claude-authwindow013"'),
]:
    assert g.count(before) == 1, f'gradle anchor mismatch: {before}'
    g = g.replace(before, after)
p.write_text(g)

p = work / 'app/src/main/AndroidManifest.xml'
m = p.read_text()
old_label = 'android:label="NEXUS C002 CLAUDE AUTH STABILITY 012"'
assert m.count(old_label) == 1, 'manifest label mismatch'
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE AUTH WINDOW 013"'))

main = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()

assert s.count('import android.view.View\n') == 1
s = s.replace('import android.view.View\n', 'import android.view.View\nimport android.view.ViewGroup\n')

state_anchor = '    private var authenticatedStableReason: String? = null\n'
assert s.count(state_anchor) == 1
s = s.replace(state_anchor, state_anchor +
    '    private var authPopupWebView: WebView? = null\n'
    '    private var authPopupSawExternalAuthHost = false\n')

chrome_start = '        webView.webChromeClient = object : WebChromeClient() {\n'
chrome_end = '\n        webView.webViewClient = object : WebViewClient() {\n'
start = s.index(chrome_start)
end = s.index(chrome_end, start)
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
                    detail = "dialog=$isDialog;user_gesture=$isUserGesture"
                )
                if (executionStarted && !terminalReceived) {
                    block("EXECUTION_NEW_WINDOW_REQUESTED")
                    return false
                }
                if (proofStopped) return false
                if (!isUserGesture) {
                    block("ANDROID_AUTH_WINDOW_REQUIRES_USER_GESTURE")
                    return false
                }
                if (authPopupWebView != null) {
                    recordDiagnostic(
                        event = "AUTH_WINDOW_ALREADY_OPEN",
                        rawUrl = view?.url,
                        detail = "single_auxiliary_window=true"
                    )
                    authPopupWebView?.requestFocus(View.FOCUS_DOWN)
                    return false
                }
                val transport = resultMsg?.obj as? WebView.WebViewTransport ?: run {
                    block("ANDROID_AUTH_WINDOW_TRANSPORT_MISSING")
                    return false
                }
                val popup = WebView(this@MainActivity)
                WebViewCompat.setProfile(popup, PROFILE_NAME)
                hardenWebView(popup)
                configureAuthPopup(popup)
                authPopupSawExternalAuthHost = false
                authPopupWebView = popup
                addContentView(
                    popup,
                    ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                )
                popup.requestFocus(View.FOCUS_DOWN)
                transport.webView = popup
                resultMsg.sendToTarget()
                recordDiagnostic(
                    event = "AUTH_WINDOW_OPENED",
                    rawUrl = view?.url,
                    detail = "profile=$PROFILE_NAME;single_auxiliary_window=true"
                )
                currentHeadline = AUTH_WINDOW_ACTIVE_HEADLINE
                currentBody = null
                renderStatus()
                return true
            }
        }
'''
s = s[:start] + new_chrome + s[end:]

helper_anchor = '    private fun handleBridgeMessage(origin: String, payload: String) {\n'
assert s.count(helper_anchor) == 1
helpers = '''    private fun configureAuthPopup(popup: WebView) {
        popup.webChromeClient = object : WebChromeClient() {
            override fun onCreateWindow(
                view: WebView?,
                isDialog: Boolean,
                isUserGesture: Boolean,
                resultMsg: Message?
            ): Boolean {
                recordDiagnostic(
                    event = "AUTH_WINDOW_NESTED_REQUEST",
                    rawUrl = view?.url,
                    detail = "dialog=$isDialog;user_gesture=$isUserGesture"
                )
                block("ANDROID_AUTH_WINDOW_NESTED_WINDOW_BLOCKED")
                return false
            }

            override fun onCloseWindow(window: WebView?) {
                closeAuthPopup("provider_window_close", reloadMain = true)
            }
        }

        popup.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val rawUrl = request.url.toString()
                val allowed = OriginPolicy.isTopLevelNavigationAllowed(rawUrl)
                val host = sanitizeHost(rawUrl)
                recordDiagnostic(
                    event = "AUTH_WINDOW_NAVIGATION",
                    rawUrl = rawUrl,
                    detail = "main_frame=${request.isForMainFrame};allowed=$allowed"
                )
                if (!request.isForMainFrame) return false
                if (!allowed) {
                    block("ANDROID_AUTH_WINDOW_ORIGIN_BLOCKED:$host")
                    return true
                }
                if (isExternalAuthHost(host)) authPopupSawExternalAuthHost = true
                return false
            }

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                val host = sanitizeHost(url)
                if (isExternalAuthHost(host)) authPopupSawExternalAuthHost = true
                recordDiagnostic(
                    event = "AUTH_WINDOW_PAGE_STARTED",
                    rawUrl = url,
                    detail = "external_auth_seen=$authPopupSawExternalAuthHost"
                )
            }

            override fun onPageFinished(view: WebView, url: String) {
                val host = sanitizeHost(url)
                recordDiagnostic(
                    event = "AUTH_WINDOW_PAGE_FINISHED",
                    rawUrl = url,
                    detail = "external_auth_seen=$authPopupSawExternalAuthHost"
                )
                if (authPopupSawExternalAuthHost && isClaudeHost(host)) {
                    recordDiagnostic(
                        event = "AUTH_WINDOW_RETURNED_TO_CLAUDE",
                        rawUrl = url,
                        detail = "settle_ms=$AUTH_POPUP_RETURN_SETTLE_MS"
                    )
                    handler.postDelayed({
                        if (authPopupWebView === popup && !executionStarted && !proofStopped) {
                            closeAuthPopup("oauth_returned_claude", reloadMain = true)
                        }
                    }, AUTH_POPUP_RETURN_SETTLE_MS)
                }
            }

            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (!request.isForMainFrame) return
                recordDiagnostic(
                    event = "AUTH_WINDOW_WEB_ERROR",
                    rawUrl = request.url.toString(),
                    detail = "code=${error.errorCode}"
                )
                block("ANDROID_AUTH_WINDOW_WEB_ERROR_${error.errorCode}")
            }

            override fun onReceivedHttpError(
                view: WebView,
                request: WebResourceRequest,
                errorResponse: WebResourceResponse
            ) {
                if (!request.isForMainFrame || errorResponse.statusCode < 400) return
                recordDiagnostic(
                    event = "AUTH_WINDOW_HTTP_ERROR",
                    rawUrl = request.url.toString(),
                    detail = "status=${errorResponse.statusCode}"
                )
                block("ANDROID_AUTH_WINDOW_HTTP_${errorResponse.statusCode}")
            }
        }
    }

    private fun closeAuthPopup(reason: String, reloadMain: Boolean) {
        val popup = authPopupWebView ?: return
        authPopupWebView = null
        authPopupSawExternalAuthHost = false
        recordDiagnostic(
            event = "AUTH_WINDOW_CLOSED",
            rawUrl = popup.url,
            detail = "reason=${sanitizeCode(reason)};reload_main=$reloadMain"
        )
        runCatching { (popup.parent as? ViewGroup)?.removeView(popup) }
        runCatching { popup.stopLoading() }
        runCatching { popup.destroy() }
        if (reloadMain && !executionStarted && !proofStopped) {
            handler.postDelayed({
                if (!executionStarted && !proofStopped && authPopupWebView == null) {
                    recordDiagnostic(
                        event = "AUTH_WINDOW_MAIN_RELOAD",
                        rawUrl = webView.url,
                        detail = "shared_profile=true"
                    )
                    webView.reload()
                }
            }, AUTH_POPUP_MAIN_RELOAD_DELAY_MS)
        }
    }

    private fun disposeAuthPopup() {
        val popup = authPopupWebView ?: return
        authPopupWebView = null
        authPopupSawExternalAuthHost = false
        runCatching { (popup.parent as? ViewGroup)?.removeView(popup) }
        runCatching { popup.stopLoading() }
        runCatching { popup.destroy() }
    }

    private fun isExternalAuthHost(host: String): Boolean =
        host == "accounts.google.com" ||
            host == "accounts.youtube.com" ||
            host == "accounts.google.fr"

    private fun isClaudeHost(host: String): Boolean =
        host == "claude.ai" || host.endsWith(".claude.ai")

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (authPopupWebView != null) {
            closeAuthPopup("user_back", reloadMain = false)
            return
        }
        super.onBackPressed()
    }

'''
s = s.replace(helper_anchor, helpers + helper_anchor)

descriptor_anchor = '        val descriptor = BridgeDescriptor(\n'
assert s.count(descriptor_anchor) == 1
s = s.replace(descriptor_anchor,
'''        if (authPopupWebView != null) {
            recordDiagnostic(
                "AUTH_STABILITY_WAIT_AUTH_WINDOW_CLOSE",
                origin,
                "no_describe_or_dispatch=true"
            )
            currentHeadline = AUTH_WINDOW_ACTIVE_HEADLINE
            currentBody = null
            renderStatus()
            return
        }

''' + descriptor_anchor)

start_anchor = '''    private fun startExecutionProof(origin: String) {
        if (!describePassed || executionStarted || proofStopped) return
'''
assert s.count(start_anchor) == 1
s = s.replace(start_anchor,
'''    private fun startExecutionProof(origin: String) {
        if (!describePassed || executionStarted || proofStopped) return
        if (authPopupWebView != null) {
            block("ANDROID_AUTH_WINDOW_STILL_OPEN_AT_EXECUTION")
            return
        }
''')

block_anchor = '''    private fun block(code: String) {
        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")
'''
assert s.count(block_anchor) == 1
s = s.replace(block_anchor,
'''    private fun block(code: String) {
        disposeAuthPopup()
        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")
''')

for before, after in [
    ('nexus_provider_profile_c002_claude_authstability012', 'nexus_provider_profile_c002_claude_authwindow013'),
    ('V005-C002-CLAUDE-AUTH-STABILITY-012-BRIDGE-001', 'V005-C002-CLAUDE-AUTH-WINDOW-013-BRIDGE-001'),
    ('V005-C002-CLAUDE-AUTH-STABILITY-012-001', 'V005-C002-CLAUDE-AUTH-WINDOW-013-001'),
    ('V005-C002-CLAUDE-AUTH-STABILITY-012-COMP-001', 'V005-C002-CLAUDE-AUTH-WINDOW-013-COMP-001'),
    ('V005_CLAUDE_AUTH_STABILITY_012_V1', 'V005_CLAUDE_AUTH_WINDOW_013_V1'),
    ('NEXUS_CLAUDE_AUTH_STABILITY_012_OK', 'NEXUS_CLAUDE_AUTH_WINDOW_013_OK'),
    ('this Android Claude auth-stability transport proof', 'this Android Claude auth-window transport proof'),
    ('.put("contract", "V005-C002-CLAUDE-AUTH-STABILITY-012")', '.put("contract", "V005-C002-CLAUDE-AUTH-WINDOW-013")'),
    ('CLAUDE AUTH STABILITY 012 — waiting for stable authenticated Claude before DESCRIBE', 'CLAUDE AUTH WINDOW 013 — authenticate in the isolated NEXUS window; execution remains blocked until it closes'),
]:
    assert before in s, f'identity/content anchor missing: {before}'
    s = s.replace(before, after)

headline_anchor = '        const val AUTH_STABILIZING_HEADLINE = "CLAUDE AUTH SIGNAL STABILIZING — no DESCRIBE or dispatch yet"\n'
assert s.count(headline_anchor) == 1
s = s.replace(headline_anchor, headline_anchor +
    '        const val AUTH_WINDOW_ACTIVE_HEADLINE = "CLAUDE AUTH WINDOW 013 — authentication window active — no DESCRIBE or dispatch"\n'
    '        const val AUTH_POPUP_RETURN_SETTLE_MS = 1_500L\n'
    '        const val AUTH_POPUP_MAIN_RELOAD_DELAY_MS = 250L\n')

main.write_text(s)
