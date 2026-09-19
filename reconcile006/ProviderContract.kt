package nexus.android.c002.provider

data class ProviderManifest(
    val id: String,
    val displayName: String,
    val homeUrl: String,
    val adapterId: String,
    val executionEnabled: Boolean
)

data class ProviderRequest(
    val requestId: String,
    val prompt: String
)

data class ProviderResult(
    val requestId: String,
    val providerId: String,
    val ok: Boolean,
    val responseText: String?,
    val errorCode: String?
)

interface ProviderAdapter {
    val manifest: ProviderManifest
    fun prepare(): Boolean
    fun send(request: ProviderRequest): Boolean
    fun cancel(requestId: String)
}

object ProviderCatalog {
    val builtIns: List<ProviderManifest> = listOf(
        ProviderManifest("chatgpt", "ChatGPT", "https://chatgpt.com/", "chatgpt_web_v1", true),
        ProviderManifest("gemini", "Gemini", "https://gemini.google.com/", "gemini_web_v1", false),
        ProviderManifest("claude", "Claude", "https://claude.ai/", "claude_web_v1", false),
        ProviderManifest("zai", "Z.ai", "https://chat.z.ai/", "zai_web_v1", false),
        ProviderManifest("grok", "Grok", "https://grok.com/", "grok_web_v1", false),
        ProviderManifest("deepseek", "DeepSeek", "https://chat.deepseek.com/", "deepseek_web_v1", false)
    )
}
