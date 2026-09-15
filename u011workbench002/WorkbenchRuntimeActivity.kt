package nexus.android.c002

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.webkit.WebResourceRequest
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
import nexus.android.c002.core.ExecutionJob
import nexus.android.c002.core.ExecutionReceiptMetadata
import nexus.android.c002.core.ProviderMetadata
import nexus.android.c002.core.RuntimeGate
import nexus.android.c002.core.SelectedProvider
import nexus.android.c002.core.U002Monitor
import nexus.android.c002.web.NexusWebBridge
import nexus.android.c002.web.OriginPolicy
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

class WorkbenchRuntimeActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var status: TextView
    private var bridge: NexusWebBridge? = null
    private val handler = Handler(Looper.getMainLooper())
    private val engine = AndroidTransportEngine()
    private lateinit var monitor: U002Monitor

    private lateinit var request: JSONObject
    private var job: ExecutionJob? = null
    private var executionStarted = false
    private var ackPassed = false
    private var terminalReceived = false
    private var finished = false
    private val bridgeRunId = "U011-WB-" + UUID.randomUUID().toString()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.providerWebView)
        status = findViewById(R.id.status)
        monitor = U002Monitor(this)

        val raw = intent.getStringExtra(EXTRA_REQUEST_JSON).orEmpty()
        request = runCatching { JSONObject(raw) }.getOrElse {
            failAndReturn("ANDROID_ANALYSIS_PAYLOAD_MALFORMED")
            return
        }
        if (request.optString("analysis_id").isBlank() || request.optString("question").isBlank()) {
            failAndReturn("ANDROID_ANALYSIS_PAYLOAD_INCOMPLETE")
            return
        }

        monitor.record("WORKBENCH_ANALYSIS_RUNTIME_START", mapOf(
            "analysis_id" to request.optString("analysis_id"),
            "subject_id" to request.optString("subject_id"),
            "provider_family" to "OPENAI",
            "transport" to TRANSPORT_ID
        ))

        if (!WebViewFeature.isFeatureSupported(WebViewFeature.MULTI_PROFILE)) {
            failAndReturn("ANDROID_WEBKIT_FEATURE_MISSING:MULTI_PROFILE")
            return
        }
        WebViewCompat.setProfile(webView, PROFILE_NAME)
        hardenWebView(webView)

        val chatGptAdapter = assets.open("u011/chatgpt_workbench_u011.js").bufferedReader().use { it.readText() }
        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }
        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }
        val zaiAdapter = assets.open("nexus/zai_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter, zaiAdapter)
        if (!install.pass) {
            failAndReturn(install.code)
            return
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                return if (OriginPolicy.isTopLevelNavigationAllowed(url)) {
                    false
                } else {
                    failAndReturn("ANDROID_NAVIGATION_ORIGIN_BLOCKED")
                    true
                }
            }

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                if (!executionStarted) {
                    bridge?.clearForNavigation()
                    status.text = "ChatGPT — chargement / authentification"
                }
            }
        }

        status.text = "NEXUS Analyse — ChatGPT\nAuthentifiez-vous si nécessaire; l'analyse démarrera automatiquement."
        webView.loadUrl("$CHATGPT_ORIGIN/")
    }

    private fun handleBridgeMessage(origin: String, payload: String) {
        if (finished) return
        val message = runCatching { JSONObject(payload) }.getOrElse {
            failAndReturn("ANDROID_BRIDGE_MESSAGE_MALFORMED")
            return
        }
        if (message.optString("channel") != CHANNEL) return

        when (message.optString("type")) {
            "CHATGPT_STATUS" -> handleStatus(origin, message)
            "PROVIDER_ACK" -> handleAck(message)
            "PROVIDER_PROGRESS" -> handleProgress(message)
            "PROVIDER_RESULT" -> handleResult(origin, message)
        }
    }

    private fun handleStatus(origin: String, message: JSONObject) {
        if (executionStarted || finished) return
        val auth = message.optJSONObject("status") ?: return
        val authState = auth.optString("state", "UNKNOWN")
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
                status.text = "ChatGPT — authentification requise\nConnectez-vous dans la page ci-dessous."
            } else {
                failAndReturn(gate.code)
            }
            return
        }
        startExecution(origin)
    }

    private fun startExecution(origin: String) {
        if (executionStarted || finished) return
        val analysisId = request.optString("analysis_id")
        val subjectId = request.optString("subject_id")
        val question = request.optString("question")
        val previousContext = request.optString("previous_context")
        val handoff = JSONObject()
            .put("mode", "ANALYSIS")
            .put("analysis_id", analysisId)
            .put("subject_id", subjectId)
            .put("previous_context", previousContext)
            .toString()

        val built = runCatching {
            engine.buildJob(
                ExecutionInput(
                    requestId = request.optString("request_id", analysisId),
                    question = question,
                    handoffText = handoff,
                    provider = SelectedProvider.CHATGPT,
                    model = null,
                    externalResearch = false
                )
            )
        }.getOrElse {
            failAndReturn("ANDROID_JOB_BUILD_FAILED")
            return
        }
        job = built
        executionStarted = true

        val frozenPackage = JSONObject()
            .put("pack_id", built.contextPackId)
            .put("analysis_id", analysisId)
            .put("subject_id", subjectId)
            .put("mode", "ANALYSIS")
            .put("question", question)
            .put("previous_context", previousContext)
            .put("audit", JSONObject()
                .put("external_research", false)
                .put("canonical_write", false)
                .put("state_mutation_mode", "NONE")
                .put("truth_winner", "NONE"))
            .put("output_contract", JSONObject()
                .put("result_pack_version", RESULT_PACK_VERSION)
                .put("comparison_id", comparisonId(analysisId))
                .put("required_fields", JSONArray(listOf(
                    "result_pack_version", "pack_id", "comparison_id", "analysis_id",
                    "subject_id", "model", "answer", "audit"
                ))))

        val envelope = JSONObject()
            .put("job_id", built.jobId)
            .put("context_pack_id", built.contextPackId)
            .put("frozen_fingerprint", built.frozenFingerprint)
            .put("provider_family", built.providerFamily)
            .put("adapter_id", built.adapterId)
            .put("question", built.question)
            .put("frozen_package", frozenPackage)

        val outbound = JSONObject()
            .put("channel", CHANNEL)
            .put("type", "EXECUTE_JOB")
            .put("bridge_run_id", bridgeRunId)
            .put("envelope", envelope)

        monitor.record("WORKBENCH_ANALYSIS_DISPATCH", mapOf(
            "analysis_id" to analysisId,
            "job_id" to built.jobId,
            "context_pack_id" to built.contextPackId,
            "frozen_fingerprint" to built.frozenFingerprint,
            "provider_family" to built.providerFamily,
            "canonical_write" to false,
            "state_mutation_mode" to "NONE",
            "truth_winner" to "NONE"
        ))
        status.text = "NEXUS Analyse — envoi à ChatGPT\nAttente ACK corrélé…"
        if (bridge?.post(origin, outbound.toString()) != true) {
            failAndReturn("ANDROID_PROVIDER_POST_FAILED")
            return
        }

        handler.postDelayed({
            if (!ackPassed && !finished) failAndReturn("ANDROID_ACK_TIMEOUT")
        }, ACK_TIMEOUT_MS)
        handler.postDelayed({
            if (!terminalReceived && !finished) failAndReturn("ANDROID_TERMINAL_TIMEOUT")
        }, TERMINAL_TIMEOUT_MS)
    }

    private fun handleAck(message: JSONObject) {
        if (!executionStarted || finished) return
        if (message.optString("bridge_run_id") != bridgeRunId) {
            failAndReturn("ANDROID_ACK_CORRELATION_MISMATCH")
            return
        }
        val response = message.optJSONObject("response")
        if (response?.optBoolean("ok", false) != true) {
            failAndReturn("ANDROID_PROVIDER_ACK_REJECTED")
            return
        }
        ackPassed = true
        status.text = "ACK PASS — ChatGPT exécute l'analyse"
        monitor.record("WORKBENCH_ANALYSIS_ACK_PASS", mapOf("bridge_run_id" to bridgeRunId))
    }

    private fun handleProgress(message: JSONObject) {
        if (!executionStarted || finished) return
        if (message.optString("bridge_run_id") != bridgeRunId) return
        val state = message.optString("job_status", "RUNNING")
        status.text = "ChatGPT — $state"
    }

    private fun handleResult(origin: String, message: JSONObject) {
        if (!executionStarted || finished) return
        if (message.optString("bridge_run_id") != bridgeRunId) {
            failAndReturn("ANDROID_TERMINAL_CORRELATION_MISMATCH")
            return
        }
        if (!ackPassed) {
            failAndReturn("ANDROID_TERMINAL_BEFORE_ACK")
            return
        }
        if (!message.optBoolean("ok", false)) {
            failAndReturn("ANDROID_PROVIDER_FAILED:" + sanitizeCode(message.optString("error", "UNKNOWN")))
            return
        }
        val currentJob = job ?: run {
            failAndReturn("ANDROID_JOB_STATE_MISSING")
            return
        }
        val pack = message.optJSONObject("result_pack") ?: run {
            failAndReturn("ANDROID_RESULT_PACK_MISSING")
            return
        }
        val validation = validateResultPack(currentJob, pack)
        if (validation != "PASS") {
            failAndReturn(validation)
            return
        }

        val model = pack.optJSONObject("model")
        val modelRef = model?.optString("model", MODEL_REF) ?: MODEL_REF
        val answer = pack.optString("answer")
        val receipt = AndroidReceipt(
            status = "COMPLETED",
            jobId = currentJob.jobId,
            contextPackId = currentJob.contextPackId,
            question = currentJob.question,
            frozenFingerprint = currentJob.frozenFingerprint,
            providerMetadata = ProviderMetadata(currentJob.providerFamily, modelRef),
            executionReceipt = ExecutionReceiptMetadata(TRANSPORT_ID),
            canonicalWrite = false,
            stateMutationMode = "NONE",
            truthWinner = "NONE",
            answer = answer,
            forbiddenFields = collectForbiddenKeys(pack)
        )
        val receiptGate = engine.validateReceipt(currentJob, receipt)
        if (!receiptGate.pass) {
            failAndReturn(receiptGate.code)
            return
        }

        val uiOrigin = message.optJSONObject("provider_meta")
            ?.optString("ui_origin", origin)
            ?.trimEnd('/') ?: origin.trimEnd('/')
        if (uiOrigin != CHATGPT_ORIGIN) {
            failAndReturn("ANDROID_PROVIDER_UI_ORIGIN_MISMATCH")
            return
        }

        terminalReceived = true
        finished = true
        val result = JSONObject()
            .put("status", "COMPLETED")
            .put("analysis_id", request.optString("analysis_id"))
            .put("subject_id", request.optString("subject_id"))
            .put("job_id", currentJob.jobId)
            .put("context_pack_id", currentJob.contextPackId)
            .put("frozen_fingerprint", currentJob.frozenFingerprint)
            .put("provider_family", currentJob.providerFamily)
            .put("model_ref", modelRef)
            .put("transport", TRANSPORT_ID)
            .put("terminal_receipt", "PASS")
            .put("answer", answer)
            .put("canonical_write", false)
            .put("state_mutation_mode", "NONE")
            .put("truth_winner", "NONE")

        monitor.record("TERMINAL_RECEIPT_PASS", mapOf(
            "analysis_id" to request.optString("analysis_id"),
            "job_id" to currentJob.jobId,
            "context_pack_id" to currentJob.contextPackId,
            "frozen_fingerprint" to currentJob.frozenFingerprint,
            "provider_family" to currentJob.providerFamily,
            "transport" to TRANSPORT_ID,
            "canonical_write" to false,
            "state_mutation_mode" to "NONE",
            "truth_winner" to "NONE",
            "status" to "COMPLETED"
        ))
        status.text = "TERMINAL RECEIPT PASS\nRetour automatique vers le fil NEXUS…"
        handler.postDelayed({
            setResult(RESULT_OK, Intent().putExtra(EXTRA_RESULT_JSON, result.toString()))
            finish()
        }, 900L)
    }

    private fun validateResultPack(currentJob: ExecutionJob, pack: JSONObject): String {
        if (pack.optString("result_pack_version") != RESULT_PACK_VERSION) return "ANDROID_RESULT_PACK_VERSION_MISMATCH"
        if (pack.optString("pack_id") != currentJob.contextPackId) return "ANDROID_RESULT_PACK_ID_MISMATCH"
        if (pack.optString("comparison_id") != comparisonId(request.optString("analysis_id"))) return "ANDROID_RESULT_COMPARISON_ID_MISMATCH"
        if (pack.optString("analysis_id") != request.optString("analysis_id")) return "ANDROID_RESULT_ANALYSIS_ID_MISMATCH"
        if (pack.optString("subject_id") != request.optString("subject_id")) return "ANDROID_RESULT_SUBJECT_ID_MISMATCH"
        if (pack.optString("answer").isBlank()) return "ANDROID_RESULT_ANSWER_MISSING"
        val model = pack.optJSONObject("model") ?: return "ANDROID_RESULT_MODEL_MISSING"
        if (model.optString("provider") != "OpenAI") return "ANDROID_RESULT_PROVIDER_MODEL_MISMATCH"
        if (model.optString("model").isBlank()) return "ANDROID_RESULT_MODEL_REF_MISSING"
        val audit = pack.optJSONObject("audit") ?: return "ANDROID_RESULT_AUDIT_MISSING"
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
            setSupportMultipleWindows(false)
        }
        WebView.setWebContentsDebuggingEnabled(false)
    }

    private fun failAndReturn(code: String) {
        if (finished) return
        finished = true
        monitor.record("WORKBENCH_ANALYSIS_FAIL_CLOSED", mapOf(
            "analysis_id" to if (::request.isInitialized) request.optString("analysis_id") else "",
            "error" to code
        ))
        if (::status.isInitialized) status.text = "BLOCKED — $code"
        if (::webView.isInitialized) webView.visibility = View.VISIBLE
        val result = JSONObject()
            .put("status", "FAILED")
            .put("analysis_id", if (::request.isInitialized) request.optString("analysis_id") else "")
            .put("subject_id", if (::request.isInitialized) request.optString("subject_id") else "")
            .put("error", code)
        handler.postDelayed({
            setResult(RESULT_CANCELED, Intent().putExtra(EXTRA_RESULT_JSON, result.toString()))
            finish()
        }, 900L)
    }

    private fun comparisonId(analysisId: String): String = "U011-ANALYSIS-$analysisId"

    private fun sanitizeCode(value: String): String =
        value.uppercase().replace(Regex("[^A-Z0-9_:-]"), "_").take(160)

    companion object {
        const val EXTRA_REQUEST_JSON = "nexus_u011_request_json"
        const val EXTRA_RESULT_JSON = "nexus_u011_result_json"
        const val PROFILE_NAME = "nexus_provider_profile_u011_workbench"
        const val CHATGPT_ORIGIN = "https://chatgpt.com"
        const val CHANNEL = "NEXUS_U011_CHATGPT_WORKBENCH_V1"
        const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"
        const val RESULT_PACK_VERSION = "U011_WORKBENCH_RESULT_V1"
        const val MODEL_REF = "ChatGPT UI session — exact backend model not exposed by bridge"
        const val ACK_TIMEOUT_MS = 5_000L
        const val TERMINAL_TIMEOUT_MS = 190_000L
    }
}
