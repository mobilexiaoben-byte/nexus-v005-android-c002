package nexus.android.c002

import android.app.Activity
import android.net.Uri
import android.os.Bundle
import android.os.Message
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.TextView
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import nexus.android.c002.core.BridgeDescriptor
import nexus.android.c002.core.RuntimeGate
import nexus.android.c002.web.NexusWebBridge
import nexus.android.c002.web.OriginPolicy
import org.json.JSONObject

class MainActivity : Activity() {
    private data class DiagnosticEvent(
        val sequence: Int,
        val fingerprint: String,
        val line: String,
        var repeatCount: Int = 1
    )

    private lateinit var webView: WebView
    private lateinit var status: TextView
    private var bridge: NexusWebBridge? = null
    private var describePassed = false
    private var diagnosticStopped = false
    private var diagnosticSequence = 0
    private val diagnosticEvents = mutableListOf<DiagnosticEvent>()
    private var diagnosticExpanded = false
    private var currentHeadline = ACTIVE_HEADLINE
    private var currentBody: String? = null
    private var lastAuthState: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.providerWebView)
        status = findViewById(R.id.status)
        status.setOnClickListener {
            diagnosticExpanded = !diagnosticExpanded
            renderStatus()
        }

        if (!WebViewFeature.isFeatureSupported(WebViewFeature.MULTI_PROFILE)) {
            block("ANDROID_WEBKIT_FEATURE_MISSING:MULTI_PROFILE")
            return
        }
        WebViewCompat.setProfile(webView, PROFILE_NAME)

        hardenWebView(webView)
        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }
        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter)
        if (!install.pass) {
            block(install.code)
            return
        }

        webView.webChromeClient = object : WebChromeClient() {
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
                block("AUTHFLOW_NEW_WINDOW_REQUESTED")
                return false
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val rawUrl = request.url.toString()
                val allowed = OriginPolicy.isTopLevelNavigationAllowed(rawUrl)
                recordDiagnostic(
                    event = "shouldOverrideUrlLoading",
                    rawUrl = rawUrl,
                    detail = "main_frame=${request.isForMainFrame};method=${request.method};redirect=${request.isRedirect};gesture=${request.hasGesture()};allowed=$allowed"
                )
                return if (allowed) {
                    false
                } else {
                    block("ANDROID_NAVIGATION_ORIGIN_BLOCKED:${sanitizeHost(rawUrl)}")
                    true
                }
            }

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                describePassed = false
                lastAuthState = null
                bridge?.clearForNavigation()
                currentHeadline = ACTIVE_HEADLINE
                currentBody = null
                recordDiagnostic("onPageStarted", url, "main_frame=true")
            }

            override fun onPageFinished(view: WebView, url: String) {
                recordDiagnostic("onPageFinished", url, "main_frame=true")
            }

            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                recordDiagnostic(
                    event = "onReceivedError",
                    rawUrl = request.url.toString(),
                    detail = "main_frame=${request.isForMainFrame};code=${error.errorCode}"
                )
                if (request.isForMainFrame) {
                    block("AUTHFLOW_MAIN_FRAME_WEB_ERROR_${error.errorCode}")
                }
            }

            override fun onReceivedHttpError(
                view: WebView,
                request: WebResourceRequest,
                errorResponse: WebResourceResponse
            ) {
                val statusCode = errorResponse.statusCode
                recordDiagnostic(
                    event = "onReceivedHttpError",
                    rawUrl = request.url.toString(),
                    detail = "main_frame=${request.isForMainFrame};status=$statusCode"
                )
                if (request.isForMainFrame && statusCode >= 400) {
                    block("AUTHFLOW_MAIN_FRAME_HTTP_$statusCode")
                }
            }
        }

        renderStatus()
        webView.loadUrl(CHATGPT_ORIGIN + "/")
    }

    private fun handleBridgeMessage(origin: String, payload: String) {
        if (describePassed || diagnosticStopped) return
        val message = runCatching { JSONObject(payload) }.getOrElse {
            block("ANDROID_DESCRIBE_MESSAGE_MALFORMED")
            return
        }
        if (message.optString("type") != "CHATGPT_STATUS") return
        if (message.optString("channel") != CHATGPT_CHANNEL) {
            block("ANDROID_DESCRIBE_CHANNEL_MISMATCH")
            return
        }
        val auth = message.optJSONObject("status") ?: run {
            block("ANDROID_DESCRIBE_STATUS_MISSING")
            return
        }
        val authState = auth.optString("state", "UNKNOWN")
        val authChanged = authState != lastAuthState
        if (authChanged) {
            lastAuthState = authState
            recordDiagnostic("bridgeStatus", origin, "auth_state=$authState")
        }

        val descriptor = BridgeDescriptor(
            authenticated = authState == "AUTHENTICATED",
            origin = origin,
            targetCount = 1,
            adapterReady = true,
            missingFeatures = emptySet()
        )
        val gate = RuntimeGate.validateDescriptor(descriptor, CHATGPT_ORIGIN)
        val out = JSONObject()
            .put("contract", "NEXUS_ANDROID_DESCRIBE_C002")
            .put("diagnostic", "V005-C002-AUTHFLOWDIAG003-DEVICE-001")
            .put("provider_family", "OPENAI")
            .put("adapter_id", "ADP-OPENAI-FAMILY")
            .put("origin", origin)
            .put("authenticated", descriptor.authenticated)
            .put("auth_state", authState)
            .put("target_count", descriptor.targetCount)
            .put("adapter_ready", descriptor.adapterReady)
            .put("model_ref", "ChatGPT UI session — exact backend model not exposed by bridge")
            .put("external_research", false)
            .put("canonical_write", false)
            .put("state_mutation_mode", "NONE")
            .put("truth_winner", "NONE")
            .put("gate", gate.code)

        if (!gate.pass) {
            if (gate.code == "ANDROID_AUTH_REQUIRED") {
                if (authChanged || currentHeadline != AUTH_REQUIRED_HEADLINE) {
                    currentHeadline = AUTH_REQUIRED_HEADLINE
                    currentBody = null
                    renderStatus()
                }
            } else {
                block("DESCRIBE_${gate.code}")
            }
            return
        }

        describePassed = true
        recordDiagnostic("DESCRIBE_PASS", origin, "authenticated=true")
        diagnosticStopped = true
        currentHeadline = "DESCRIBE PASS — STOP GATE"
        currentBody = out.toString(2)
        renderStatus()
        // Deliberately no provider job dispatch here. V-005 runtime proof must stop after DESCRIBE.
    }

    private fun hardenWebView(view: WebView) {
        with(view.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            // Diagnostic-only: surface popup/new-window attempts through WebChromeClient.onCreateWindow.
            // The callback always returns false; no secondary WebView is created and no host is added.
            setSupportMultipleWindows(true)
            javaScriptCanOpenWindowsAutomatically = false
        }
        WebView.setWebContentsDebuggingEnabled(false)
    }

    private fun recordDiagnostic(event: String, rawUrl: String?, detail: String? = null) {
        if (diagnosticStopped) return
        val urlPart = if (rawUrl.isNullOrBlank()) "" else "url=${sanitizeUrl(rawUrl)} host=${sanitizeHost(rawUrl)}"
        val detailPart = detail.orEmpty()
        val fingerprint = "$event|$urlPart|$detailPart"
        val previous = diagnosticEvents.lastOrNull()
        if (previous?.fingerprint == fingerprint) {
            previous.repeatCount += 1
            return
        }

        diagnosticSequence += 1
        val line = buildString {
            append(diagnosticSequence)
            append(" ")
            append(event)
            if (urlPart.isNotBlank()) {
                append(" ")
                append(urlPart)
            }
            if (detailPart.isNotBlank()) {
                append(" ")
                append(detailPart)
            }
        }
        diagnosticEvents.add(DiagnosticEvent(diagnosticSequence, fingerprint, line))
        while (diagnosticEvents.size > MAX_DIAGNOSTIC_EVENTS) diagnosticEvents.removeAt(0)
        renderStatus()
    }

    private fun sanitizeUrl(rawUrl: String): String {
        val uri = runCatching { Uri.parse(rawUrl) }.getOrNull() ?: return "<invalid>"
        val scheme = uri.scheme?.lowercase() ?: "<no-scheme>"
        val host = uri.host?.lowercase() ?: "<no-host>"
        val port = uri.port
        val portPart = if (port > 0 && !isDefaultPort(scheme, port)) ":$port" else ""
        val pathDepth = uri.pathSegments?.size ?: 0
        val pathShape = if (pathDepth == 0) "/" else "/<path:$pathDepth>"
        return "$scheme://$host$portPart$pathShape"
    }

    private fun sanitizeHost(rawUrl: String): String {
        val uri = runCatching { Uri.parse(rawUrl) }.getOrNull() ?: return "<invalid>"
        return uri.host?.lowercase() ?: "<no-host>"
    }

    private fun isDefaultPort(scheme: String, port: Int): Boolean =
        (scheme == "https" && port == 443) || (scheme == "http" && port == 80)

    private fun renderStatus() {
        status.maxLines = if (diagnosticExpanded) EXPANDED_STATUS_LINES else COMPACT_STATUS_LINES
        status.text = buildString {
            append(currentHeadline)
            val visibleEvents = if (diagnosticExpanded) diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT) else diagnosticEvents.takeLast(1)
            visibleEvents.forEach { event ->
                append("\n")
                append(event.line)
                if (event.repeatCount > 1) append(" ×").append(event.repeatCount)
            }
            if (diagnosticExpanded && !currentBody.isNullOrBlank()) {
                append("\n")
                append(currentBody)
            }
        }
    }

    private fun block(code: String) {
        if (!diagnosticStopped && ::status.isInitialized) {
            diagnosticSequence += 1
            diagnosticEvents.add(
                DiagnosticEvent(
                    diagnosticSequence,
                    "STOP|$code",
                    "$diagnosticSequence STOP code=$code"
                )
            )
            while (diagnosticEvents.size > MAX_DIAGNOSTIC_EVENTS) diagnosticEvents.removeAt(0)
        }
        diagnosticStopped = true
        currentHeadline = "BLOCKED — $code"
        currentBody = null
        if (::status.isInitialized) renderStatus()
        if (::webView.isInitialized) webView.visibility = View.GONE
    }

    companion object {
        const val PROFILE_NAME = "nexus_provider_profile_c002_authflowdiag003"
        const val CHATGPT_ORIGIN = "https://chatgpt.com"
        const val CHATGPT_CHANNEL = "NEXUS_POC022_C8B2R1"
        const val MAX_DIAGNOSTIC_EVENTS = 12
        const val EXPANDED_EVENT_COUNT = 4
        const val COMPACT_STATUS_LINES = 2
        const val EXPANDED_STATUS_LINES = 8
        const val ACTIVE_HEADLINE = "AUTHFLOWDIAG003 ACTIVE — ChatGPT remains usable; tap status to expand"
        const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — use ChatGPT sign-in below; tap status for diagnostics"
    }
}
