package nexus.android.c002

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import org.json.JSONObject

class WorkbenchActivity : Activity() {
    private lateinit var webView: WebView
    private var pendingAnalysisId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        setContentView(webView)
        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            setSupportMultipleWindows(false)
        }
        WebView.setWebContentsDebuggingEnabled(false)
        webView.addJavascriptInterface(AndroidBridge(), "NexusAndroid")
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                return !url.startsWith("file:///android_asset/u011/")
            }
        }
        webView.loadUrl("file:///android_asset/u011/workbench.html")
    }

    @Deprecated("Deprecated in Java")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != ANALYSIS_REQUEST_CODE) return
        val payload = data?.getStringExtra(WorkbenchRuntimeActivity.EXTRA_RESULT_JSON)
        if (resultCode == RESULT_OK && !payload.isNullOrBlank()) {
            deliverJs("window.NexusWorkbench&&window.NexusWorkbench.onRuntimeResult", payload)
        } else {
            val errorPayload = if (!payload.isNullOrBlank()) payload else JSONObject()
                .put("analysis_id", pendingAnalysisId.orEmpty())
                .put("error", "ANDROID_RUNTIME_CANCELLED")
                .toString()
            deliverJs("window.NexusWorkbench&&window.NexusWorkbench.onRuntimeError", errorPayload)
        }
        pendingAnalysisId = null
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    private fun deliverJs(functionExpression: String, payload: String) {
        val quoted = JSONObject.quote(payload)
        webView.post {
            webView.evaluateJavascript("$functionExpression($quoted);", null)
        }
    }

    inner class AndroidBridge {
        @JavascriptInterface
        fun getPlatform(): String = "ANDROID"

        @JavascriptInterface
        fun openProviderRuntime() {
            runOnUiThread {
                startActivity(Intent(this@WorkbenchActivity, MainActivity::class.java))
            }
        }

        @JavascriptInterface
        fun runAnalysis(payloadJson: String) {
            val payload = runCatching { JSONObject(payloadJson) }.getOrElse {
                val error = JSONObject()
                    .put("analysis_id", "")
                    .put("error", "ANDROID_ANALYSIS_PAYLOAD_MALFORMED")
                    .toString()
                deliverJs("window.NexusWorkbench&&window.NexusWorkbench.onRuntimeError", error)
                return
            }
            val analysisId = payload.optString("analysis_id")
            val question = payload.optString("question")
            if (analysisId.isBlank() || question.isBlank()) {
                val error = JSONObject()
                    .put("analysis_id", analysisId)
                    .put("error", "ANDROID_ANALYSIS_PAYLOAD_INCOMPLETE")
                    .toString()
                deliverJs("window.NexusWorkbench&&window.NexusWorkbench.onRuntimeError", error)
                return
            }
            pendingAnalysisId = analysisId
            runOnUiThread {
                startActivityForResult(
                    Intent(this@WorkbenchActivity, WorkbenchRuntimeActivity::class.java)
                        .putExtra(WorkbenchRuntimeActivity.EXTRA_REQUEST_JSON, payload.toString()),
                    ANALYSIS_REQUEST_CODE
                )
            }
        }
    }

    companion object {
        const val ANALYSIS_REQUEST_CODE = 1102
    }
}
