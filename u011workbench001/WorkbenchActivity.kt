package nexus.android.c002

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader

class WorkbenchActivity : Activity() {
    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_workbench)
        webView = findViewById(R.id.workbenchWebView)

        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        with(webView.settings) {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            setSupportMultipleWindows(false)
        }
        WebView.setWebContentsDebuggingEnabled(false)
        webView.addJavascriptInterface(NativeBridge(), "NexusAndroid")
        webView.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest) =
                assetLoader.shouldInterceptRequest(request.url)

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                return !url.startsWith(APPASSETS_ORIGIN)
            }
        }
        webView.loadUrl(WORKBENCH_URL)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    private inner class NativeBridge {
        @JavascriptInterface
        fun openProviderRuntime() {
            runOnUiThread {
                startActivity(Intent(this@WorkbenchActivity, MainActivity::class.java))
            }
        }

        @JavascriptInterface
        fun getPlatform(): String = "ANDROID"
    }

    companion object {
        private const val APPASSETS_ORIGIN = "https://appassets.androidplatform.net/"
        private const val WORKBENCH_URL = "https://appassets.androidplatform.net/assets/nexus/workbench.html"
    }
}
