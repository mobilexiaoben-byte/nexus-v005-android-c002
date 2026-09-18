package nexus.android.c002

import android.app.Activity
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
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
import nexus.android.c002.core.AndroidReceipt
import nexus.android.c002.core.AndroidTransportEngine
import nexus.android.c002.core.BridgeDescriptor
import nexus.android.c002.core.ExecutionInput
import nexus.android.c002.core.ExecutionReceiptMetadata
import nexus.android.c002.core.ExecutionJob
import nexus.android.c002.core.ProviderMetadata
import nexus.android.c002.core.RuntimeGate
import nexus.android.c002.core.SelectedProvider
import nexus.android.c002.web.NexusWebBridge
import nexus.android.c002.web.OriginPolicy
import org.json.JSONArray
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
    private val handler = Handler(Looper.getMainLooper())
    private val engine = AndroidTransportEngine()
    private var proofJob: ExecutionJob? = null
    private var describePassed = false
    private var executionStarted = false
    private var ackPassed = false
    private var terminalReceived = false
    private var proofStopped = false
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
                block("EXECUTION_NEW_WINDOW_REQUESTED")
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
                    detail = "main_frame=${request.isForMainFrame};allowed=$allowed"
                )
                return if (allowed) {
                    false
                } else {
                    block("ANDROID_NAVIGATION_ORIGIN_BLOCKED:${sanitizeHost(rawUrl)}")
                    true
                }
            }

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                if (executionStarted && !terminalReceived) {
                    recordDiagnostic("onPageStarted", url, "execution_in_progress=true")
                } else {
                    describePassed = false
                    lastAuthState = null
                    bridge?.clearForNavigation()
                    currentHeadline = ACTIVE_HEADLINE
                    currentBody = null
                    recordDiagnostic("onPageStarted", url, "main_frame=true")
                }
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
                if (request.isForMainFrame) block("EXECUTION_MAIN_FRAME_WEB_ERROR_${error.errorCode}")
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
                if (request.isForMainFrame && statusCode >= 400) block("EXECUTION_MAIN_FRAME_HTTP_$statusCode")
            }
        }

        renderStatus()
        webView.loadUrl("$CHATGPT_ORIGIN/")
    }

    private fun handleBridgeMessage(origin: String, payload: String) {
        if (proofStopped) return
        val message = runCatching { JSONObject(payload) }.getOrElse {
            block("ANDROID_BRIDGE_MESSAGE_MALFORMED")
            return
        }
        if (message.optString("channel") != CHATGPT_CHANNEL) {
            block("ANDROID_BRIDGE_CHANNEL_MISMATCH")
            return
        }

        when (message.optString("type")) {
            "CHATGPT_STATUS" -> handleStatus(origin, message)
            "PROVIDER_ACK" -> handleProviderAck(message)
            "PROVIDER_PROGRESS" -> handleProviderProgress(message)
            "PROVIDER_RESULT" -> handleProviderResult(origin, message)
        }
    }

    private fun handleStatus(origin: String, message: JSONObject) {
        if (executionStarted || describePassed) return
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
        currentHeadline = "DESCRIBE PASS — execution proof starting"
        currentBody = null
        renderStatus()
        startExecutionProof(origin)
    }

    private fun startExecutionProof(origin: String) {
        if (!describePassed || executionStarted || proofStopped) return
        val input = ExecutionInput(
            requestId = JOB_ID,
            question = PROOF_QUESTION,
            handoffText = PROOF_HANDOFF,
            provider = SelectedProvider.CHATGPT,
            model = null,
            externalResearch = false
        )
        val job = runCatching { engine.buildJob(input) }.getOrElse {
            block("ANDROID_JOB_BUILD_FAILED")
            return
        }
        proofJob = job

        val expectedResult = JSONObject()
            .put("result_pack_version", RESULT_PACK_VERSION)
            .put("pack_id", job.contextPackId)
            .put("comparison_id", COMPARISON_ID)
            .put("model", JSONObject()
                .put("provider", "OpenAI")
                .put("model", MODEL_REF))
            .put("answer", PROOF_TOKEN)
            .put("audit", JSONObject()
                .put("external_research", false)
                .put("canonical_write", false)
                .put("state_mutation_mode", "NONE")
                .put("truth_winner", "NONE"))

        val frozenPackage = JSONObject()
            .put("result_pack_version", RESULT_PACK_VERSION)
            .put("pack_id", job.contextPackId)
            .put("comparison_id", COMPARISON_ID)
            .put("question", job.question)
            .put("frozen_fingerprint", job.frozenFingerprint)
            .put("output_contract", JSONObject().put("expected_result_pack", expectedResult))

        val envelope = JSONObject()
            .put("job_id", job.jobId)
            .put("context_pack_id", job.contextPackId)
            .put("frozen_fingerprint", job.frozenFingerprint)
            .put("provider_family", job.providerFamily)
            .put("adapter_id", job.adapterId)
            .put("question", job.question)
            .put("external_research", false)
            .put("canonical_rights", "NONE")
            .put("canonical_write", false)
            .put("state_mutation_mode", "NONE")
            .put("truth_winner", "NONE")
            .put("frozen_package", frozenPackage)

        val outbound = JSONObject()
            .put("channel", CHATGPT_CHANNEL)
            .put("type", "EXECUTE_JOB")
            .put("bridge_run_id", BRIDGE_RUN_ID)
            .put("envelope", envelope)

        executionStarted = true
        recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;external_research=false")
        currentHeadline = "EXECUTION PROOF — waiting for correlated ACK"
        currentBody = null
        renderStatus()

        if (bridge?.post(origin, outbound.toString()) != true) {
            block("ANDROID_EXECUTE_JOB_POST_FAILED")
            return
        }

        handler.postDelayed({
            if (!ackPassed && !proofStopped) block("ANDROID_ACK_TIMEOUT")
        }, ACK_TIMEOUT_MS)
        handler.postDelayed({
            if (!terminalReceived && !proofStopped) block("ANDROID_TERMINAL_TIMEOUT")
        }, TERMINAL_TIMEOUT_MS)
    }

    private fun handleProviderAck(message: JSONObject) {
        if (!executionStarted || proofStopped) return
        val correlated = message.optString("bridge_run_id") == BRIDGE_RUN_ID
        val response = message.optJSONObject("response")
        val accepted = response?.optBoolean("ok", false) == true && response.optBoolean("accepted", false)
        val gate = RuntimeGate.validateAck(received = accepted, correlated = correlated)
        if (!gate.pass) {
            block(gate.code)
            return
        }
        ackPassed = true
        recordDiagnostic("ACK_PASS", CHATGPT_ORIGIN, "bridge_run_id=$BRIDGE_RUN_ID")
        currentHeadline = "ACK PASS — provider polling ChatGPT UI"
        currentBody = null
        renderStatus()
    }

    private fun handleProviderProgress(message: JSONObject) {
        if (!executionStarted || proofStopped) return
        if (message.optString("bridge_run_id") != BRIDGE_RUN_ID) {
            block("ANDROID_PROGRESS_CORRELATION_MISMATCH")
            return
        }
        val jobStatus = message.optString("job_status", "UNKNOWN").take(96)
        recordDiagnostic("PROVIDER_PROGRESS", CHATGPT_ORIGIN, "status=$jobStatus")
        currentHeadline = "EXECUTION PROOF — $jobStatus"
        currentBody = null
        renderStatus()
    }

    private fun handleProviderResult(origin: String, message: JSONObject) {
        if (!executionStarted || proofStopped) return
        terminalReceived = true
        if (message.optString("bridge_run_id") != BRIDGE_RUN_ID) {
            block("ANDROID_TERMINAL_CORRELATION_MISMATCH")
            return
        }
        if (!ackPassed) {
            block("ANDROID_TERMINAL_BEFORE_ACK")
            return
        }
        if (!message.optBoolean("ok", false)) {
            block("ANDROID_PROVIDER_FAILED:${sanitizeCode(message.optString("error", "UNKNOWN"))}")
            return
        }
        val job = proofJob ?: run {
            block("ANDROID_JOB_STATE_MISSING")
            return
        }
        val resultPack = message.optJSONObject("result_pack") ?: run {
            block("ANDROID_RESULT_PACK_MISSING")
            return
        }

        val packValidation = validateResultPack(job, resultPack)
        if (packValidation != "PASS") {
            block(packValidation)
            return
        }

        val model = resultPack.optJSONObject("model")
        val modelRef = model?.optString("model", MODEL_REF)
        val forbidden = collectForbiddenKeys(resultPack)
        val receipt = AndroidReceipt(
            status = "COMPLETED",
            jobId = job.jobId,
            contextPackId = job.contextPackId,
            question = job.question,
            frozenFingerprint = job.frozenFingerprint,
            providerMetadata = ProviderMetadata(job.providerFamily, modelRef),
            executionReceipt = ExecutionReceiptMetadata(TRANSPORT_ID),
            canonicalWrite = false,
            stateMutationMode = "NONE",
            truthWinner = "NONE",
            answer = resultPack.optString("answer"),
            forbiddenFields = forbidden
        )
        val receiptGate = engine.validateReceipt(job, receipt)
        if (!receiptGate.pass) {
            block(receiptGate.code)
            return
        }

        val providerMeta = message.optJSONObject("provider_meta")
        val uiOrigin = providerMeta?.optString("ui_origin", origin)?.trimEnd('/') ?: origin.trimEnd('/')
        if (uiOrigin != CHATGPT_ORIGIN) {
            block("ANDROID_PROVIDER_UI_ORIGIN_MISMATCH")
            return
        }

        proofStopped = true
        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")
        currentHeadline = "EXECUTION PROOF PASS — STOP GATE"
        currentBody = JSONObject()
            .put("contract", "V005-C002-EXECUTION-PROOF-006")
            .put("job_id", job.jobId)
            .put("context_pack_id", job.contextPackId)
            .put("frozen_fingerprint", job.frozenFingerprint)
            .put("provider_family", job.providerFamily)
            .put("adapter_id", job.adapterId)
            .put("model_ref", modelRef)
            .put("transport", TRANSPORT_ID)
            .put("ack", "PASS")
            .put("terminal_receipt", "PASS")
            .put("answer", PROOF_TOKEN)
            .put("external_research", false)
            .put("canonical_write", false)
            .put("state_mutation_mode", "NONE")
            .put("truth_winner", "NONE")
            .toString(2)
        renderStatus()
    }

    private fun validateResultPack(job: ExecutionJob, resultPack: JSONObject): String {
        if (resultPack.optString("result_pack_version") != RESULT_PACK_VERSION) return "ANDROID_RESULT_PACK_VERSION_MISMATCH"
        if (resultPack.optString("pack_id") != job.contextPackId) return "ANDROID_RESULT_PACK_ID_MISMATCH"
        if (resultPack.optString("comparison_id") != COMPARISON_ID) return "ANDROID_RESULT_COMPARISON_ID_MISMATCH"
        if (resultPack.optString("answer") != PROOF_TOKEN) return "ANDROID_RESULT_ANSWER_MISMATCH"
        val model = resultPack.optJSONObject("model") ?: return "ANDROID_RESULT_MODEL_MISSING"
        if (model.optString("provider") != "OpenAI") return "ANDROID_RESULT_PROVIDER_MODEL_MISMATCH"
        if (model.optString("model") != MODEL_REF) return "ANDROID_RESULT_MODEL_REF_MISMATCH"
        val audit = resultPack.optJSONObject("audit") ?: return "ANDROID_RESULT_AUDIT_MISSING"
        if (audit.optBoolean("external_research", true)) return "ANDROID_RESULT_EXTERNAL_RESEARCH_FORBIDDEN"
        if (audit.optBoolean("canonical_write", true)) return "ANDROID_RESULT_CANONICAL_WRITE_FORBIDDEN"
        if (audit.optString("state_mutation_mode") != "NONE") return "ANDROID_RESULT_STATE_MUTATION_FORBIDDEN"
        if (audit.optString("truth_winner") != "NONE") return "ANDROID_RESULT_TRUTH_WINNER_FORBIDDEN"
        return "PASS"
    }

    private fun collectForbiddenKeys(value: Any?): Set<String> {
        val forbidden = linkedSetOf<String>()
        fun visit(v: Any?) {
            when (v) {
                is JSONObject -> {
                    val keys = v.keys()
                    while (keys.hasNext()) {
                        val key = keys.next()
                        val lower = key.lowercase()
                        if (lower.contains("password") || lower.contains("cookie") || lower.contains("token") ||
                            lower.contains("secret") || lower.contains("endpoint")) forbidden.add(key)
                        visit(v.opt(key))
                    }
                }
                is JSONArray -> for (i in 0 until v.length()) visit(v.opt(i))
            }
        }
        visit(value)
        return forbidden
    }

    private fun hardenWebView(view: WebView) {
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

    private fun recordDiagnostic(event: String, rawUrl: String?, detail: String? = null) {
        if (proofStopped) return
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
            append(diagnosticSequence).append(" ").append(event)
            if (urlPart.isNotBlank()) append(" ").append(urlPart)
            if (detailPart.isNotBlank()) append(" ").append(detailPart)
        }
        diagnosticEvents.add(DiagnosticEvent(diagnosticSequence, fingerprint, line))
        while (diagnosticEvents.size > MAX_DIAGNOSTIC_EVENTS) diagnosticEvents.removeAt(0)
        renderStatus()
    }

    private fun recordFinalEvent(event: String, detail: String) {
        diagnosticSequence += 1
        diagnosticEvents.add(DiagnosticEvent(diagnosticSequence, "$event|$detail", "$diagnosticSequence $event $detail"))
        while (diagnosticEvents.size > MAX_DIAGNOSTIC_EVENTS) diagnosticEvents.removeAt(0)
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

    private fun sanitizeCode(raw: String): String = raw.uppercase()
        .replace(Regex("[^A-Z0-9_:\\-.]"), "_")
        .take(120)

    private fun isDefaultPort(scheme: String, port: Int): Boolean =
        (scheme == "https" && port == 443) || (scheme == "http" && port == 80)

    private fun renderStatus() {
        status.maxLines = if (diagnosticExpanded) EXPANDED_STATUS_LINES else COMPACT_STATUS_LINES
        status.text = buildString {
            append(currentHeadline)
            val visibleEvents = if (diagnosticExpanded) diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT) else diagnosticEvents.takeLast(1)
            visibleEvents.forEach { event ->
                append("\n").append(event.line)
                if (event.repeatCount > 1) append(" ×").append(event.repeatCount)
            }
            if (diagnosticExpanded && !currentBody.isNullOrBlank()) append("\n").append(currentBody)
        }
    }

    private fun block(code: String) {
        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")
        proofStopped = true
        currentHeadline = "BLOCKED — $code"
        currentBody = null
        if (::status.isInitialized) renderStatus()
    }

    companion object {
        const val PROFILE_NAME = "nexus_provider_profile_c002_executionproof006"
        const val CHATGPT_ORIGIN = "https://chatgpt.com"
        const val CHATGPT_CHANNEL = "NEXUS_POC022_C8B2R1"
        const val BRIDGE_RUN_ID = "V005-C002-EXECUTION-PROOF-006-BRIDGE-001"
        const val JOB_ID = "V005-C002-EXECUTION-PROOF-006-001"
        const val COMPARISON_ID = "V005-C002-EXECUTION-PROOF-006-COMP-001"
        const val RESULT_PACK_VERSION = "V005_EXECUTION_PROOF_006_V1"
        const val PROOF_TOKEN = "NEXUS_EXECUTION_PROOF_006_OK"
        const val MODEL_REF = "ChatGPT UI session — exact backend model not exposed by bridge"
        const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"
        const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android transport proof. The answer field must be NEXUS_EXECUTION_PROOF_006_OK."
        const val PROOF_HANDOFF = "Read-only V-005 Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."
        const val ACK_TIMEOUT_MS = 5_000L
        const val TERMINAL_TIMEOUT_MS = 190_000L
        const val MAX_DIAGNOSTIC_EVENTS = 16
        const val EXPANDED_EVENT_COUNT = 6
        const val COMPACT_STATUS_LINES = 2
        const val EXPANDED_STATUS_LINES = 10
        const val ACTIVE_HEADLINE = "EXECUTION PROOF 006 — authenticate in ChatGPT; one read-only proof job will run after DESCRIBE PASS"
        const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; execution starts only after authenticated DESCRIBE PASS"
    }
}
