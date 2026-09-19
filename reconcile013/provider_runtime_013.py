from pathlib import Path
import re
import shutil
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Build on exact Runtime 012 Golden-first candidate.
exec((repo / "reconcile012" / "provider_runtime_012.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile012" / "provider_runtime_012.py"),
    "sys": sys,
})

assets = root / "app/src/main/assets/nexus"
main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
bridge_path = root / "app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt"
origin_path = root / "app/src/main/java/nexus/android/c002/web/OriginPolicy.kt"
transport_path = root / "app/src/main/java/nexus/android/c002/core/TransportContract.kt"

# ---------------------------------------------------------------------------
# Gemini — Golden-preserving execution auth:
# manual confirmation is product authority, but execution still requires a real
# visible Gemini composer. This avoids false GUEST_READY caused by stale login UI.
# ---------------------------------------------------------------------------
gemini_path = assets / "gemini_provider_c002.js"
g = gemini_path.read_text()
old = """      const auth=detectAuth();
      if(auth.state!=='AUTHENTICATED') throw new Error('GEMINI_NOT_AUTHENTICATED:'+auth.state);
      if(envelope.provider_family!=='GOOGLE') throw new Error('PROVIDER_FAMILY_NOT_GOOGLE');
"""
new = """      const auth=detectAuth();
      const composerAtDispatch=findComposer();
      const manuallyConfirmed=envelope.user_confirmed_connected===true;
      const sessionUsable=auth.state==='AUTHENTICATED'||(manuallyConfirmed&&!!composerAtDispatch);
      if(!sessionUsable) throw new Error('GEMINI_NOT_AUTHENTICATED:'+auth.state);
      if(envelope.provider_family!=='GOOGLE') throw new Error('PROVIDER_FAMILY_NOT_GOOGLE');
"""
assert old in g, "Gemini execute auth anchor missing"
g = g.replace(old, new, 1)
old = """      await progress(bridgeRunId,'GEMINI_UI_PREPARING');
      const composer=findComposer();
      if(!composer) throw new Error('GEMINI_COMPOSER_NOT_FOUND');
"""
new = """      await progress(bridgeRunId,'GEMINI_UI_PREPARING');
      const composer=composerAtDispatch||findComposer();
      if(!composer) throw new Error('GEMINI_COMPOSER_NOT_FOUND');
"""
assert old in g, "Gemini composer anchor missing"
g = g.replace(old, new, 1)
gemini_path.write_text(g)

# ---------------------------------------------------------------------------
# Claude — enable the already shipped Android bridge candidate, while preserving
# strict live Claude auth. DEVICE evidence currently shows UNAUTHENTICATED, so
# Runtime 013 must not bypass that condition.
# ---------------------------------------------------------------------------
claude_path = assets / "claude_provider_c002.js"
claude = claude_path.read_text()
m = re.search(r"const CHANNEL='([^']+)'", claude)
assert m, "Claude channel not found"
claude_channel = m.group(1)
if "type:'BRIDGE_READY'" not in claude:
    marker = "console.info("
    assert marker in claude, "Claude console marker missing"
    ready = "[0,100,300,1000].forEach((delay)=>setTimeout(()=>{nativeSend({channel:CHANNEL,type:'BRIDGE_READY'}).catch(()=>{});},delay));\n  console.info("
    claude = claude.replace(marker, ready, 1)
claude_path.write_text(claude)

# ---------------------------------------------------------------------------
# Grok — new Android candidate adapter. This is NOT a Golden/DEVICE PASS yet.
# ---------------------------------------------------------------------------
shutil.copy2(repo / "reconcile013" / "grok_provider_013.js", assets / "grok_provider_013.js")

# Transport policy adds Grok without changing historical ChatGPT/Gemini/Z.ai.
tc = transport_path.read_text()
assert "enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI, ZAI }" in tc
tc = tc.replace(
    "enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI, ZAI }",
    "enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI, ZAI, GROK }",
    1
)
anchor = '        SelectedProvider.ZAI to ProviderPolicy("ZAI", "ADP-ZAI-GLM-FAMILY", "https://chat.z.ai", true)\n'
assert anchor in tc, "ZAI provider policy anchor missing"
tc = tc.replace(
    anchor,
    anchor.rstrip("\n") + ',\n        SelectedProvider.GROK to ProviderPolicy("XAI", "ADP-XAI-GROK-FAMILY", "https://grok.com", true)\n',
    1
)
transport_path.write_text(tc)

# Bridge origin allowlist.
op = origin_path.read_text()
anchor = '        "https://chat.z.ai"\n'
assert anchor in op, "ZAI bridge origin anchor missing"
op = op.replace(anchor, '        "https://chat.z.ai",\n        "https://grok.com"\n', 1)
origin_path.write_text(op)

# Install Grok adapter alongside existing ChatGPT/Claude/Gemini/Z.ai adapters.
b = bridge_path.read_text()
old = "fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String, zaiAdapterScript: String): BridgeInstallResult {"
new = "fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String, zaiAdapterScript: String, grokAdapterScript: String): BridgeInstallResult {"
assert old in b, "bridge install signature 012 missing"
b = b.replace(old, new, 1)
anchor = """        WebViewCompat.addJavaScriptOnEvent(
            webView,
            zaiAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://chat.z.ai"),
            isolatedWorld
        )
        return BridgeInstallResult(true, "PASS")
"""
insert = """        WebViewCompat.addJavaScriptOnEvent(
            webView,
            zaiAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://chat.z.ai"),
            isolatedWorld
        )
        WebViewCompat.addJavaScriptOnEvent(
            webView,
            grokAdapterScript,
            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,
            setOf("https://grok.com"),
            isolatedWorld
        )
        return BridgeInstallResult(true, "PASS")
"""
assert anchor in b, "ZAI injection block missing"
b = b.replace(anchor, insert, 1)
bridge_path.write_text(b)

s = main_path.read_text()

old = """        val zaiAdapter = assets.open("nexus/zai_provider_c002.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter, zaiAdapter)
"""
new = """        val zaiAdapter = assets.open("nexus/zai_provider_c002.js").bufferedReader().use { it.readText() }
        val grokAdapter = assets.open("nexus/grok_provider_013.js").bufferedReader().use { it.readText() }
        bridge = NexusWebBridge(webView, ::handleBridgeMessage)
        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter, zaiAdapter, grokAdapter)
"""
assert old in s, "adapter install call 012 missing"
s = s.replace(old, new, 1)

# Accept Claude/Grok bridge messages in addition to the three already enabled.
old = 'if (message.optString("channel") != CHATGPT_CHANNEL && message.optString("channel") != GEMINI_CHANNEL && message.optString("channel") != ZAI_CHANNEL) return'
new = 'if (message.optString("channel") != CHATGPT_CHANNEL && message.optString("channel") != GEMINI_CHANNEL && message.optString("channel") != ZAI_CHANNEL && message.optString("channel") != CLAUDE_RUNTIME_CHANNEL && message.optString("channel") != GROK_CHANNEL) return'
assert old in s, "bridge channel gate 012 missing"
s = s.replace(old, new, 1)

# Provider dispatch: preserve ChatGPT PASS; enable Claude candidate and Grok candidate.
old = """            "Z.ai" -> SelectedProvider.ZAI
            "Claude" -> {
                productState.text = "Claude · limitation Android non certifiée"
                return
            }
            else -> {
"""
new = """            "Z.ai" -> SelectedProvider.ZAI
            "Claude" -> SelectedProvider.CLAUDE
            "Grok" -> SelectedProvider.GROK
            else -> {
"""
assert old in s, "provider switch 012 anchor missing"
s = s.replace(old, new, 1)

old = """            SelectedProvider.ZAI -> ZAI_CHANNEL
            else -> CHATGPT_CHANNEL
"""
new = """            SelectedProvider.ZAI -> ZAI_CHANNEL
            SelectedProvider.CLAUDE -> CLAUDE_RUNTIME_CHANNEL
            SelectedProvider.GROK -> GROK_CHANNEL
            else -> CHATGPT_CHANNEL
"""
assert old in s, "execution channel anchor missing"
s = s.replace(old, new, 1)

old = """            SelectedProvider.ZAI -> "Z.ai"
            else -> ""
"""
new = """            SelectedProvider.ZAI -> "Z.ai"
            SelectedProvider.CLAUDE -> "Anthropic"
            SelectedProvider.GROK -> "xAI"
            else -> ""
"""
assert old in s, "provider label anchor missing"
s = s.replace(old, new, 1)

# Product manual confirmation is carried to adapters, but does not bypass a
# missing composer/session. Gemini/Grok use it only with real visible composer.
envelope_anchor = '.put("research_policy", job.researchPolicy.name)\n            .put("canonical_rights", "NONE")'
assert envelope_anchor in s, "Runtime 012 M024 envelope anchor missing"
s = s.replace(
    envelope_anchor,
    '.put("research_policy", job.researchPolicy.name)\n            .put("user_confirmed_connected", providerConfirmedByUser)\n            .put("canonical_rights", "NONE")',
    1
)

# Result Pack validation for newly dispatched provider families.
old = """            "ZAI" -> "Z.ai"
            else -> return "ANDROID_RESULT_PROVIDER_FAMILY_UNSUPPORTED"
"""
new = """            "ZAI" -> "Z.ai"
            "ANTHROPIC" -> "Anthropic"
            "XAI" -> "xAI"
            else -> return "ANDROID_RESULT_PROVIDER_FAMILY_UNSUPPORTED"
"""
assert old in s, "provider family validation anchor missing"
s = s.replace(old, new, 1)

# Add explicit channels. Claude value is extracted from the actual shipped asset.
const_anchor = '        const val ZAI_CHANNEL = "NEXUS_V005_ZAI_001"\n'
assert const_anchor in s, "ZAI channel constant missing"
s = s.replace(
    const_anchor,
    const_anchor +
    f'        const val CLAUDE_RUNTIME_CHANNEL = "{claude_channel}"\n' +
    '        const val GROK_CHANNEL = "NEXUS_V007_GROK_013"\n',
    1
)

main_path.write_text(s)

# Candidate identity.
gradle = root / "app/build.gradle.kts"
x = gradle.read_text()
assert "versionCode = 65" in x
assert 'versionName = "0.0.65-v007-m024-u013-provider-runtime012-golden-replay"' in x
x = x.replace("versionCode = 65", "versionCode = 66", 1)
x = x.replace(
    'versionName = "0.0.65-v007-m024-u013-provider-runtime012-golden-replay"',
    'versionName = "0.0.66-v007-m024-u013-provider-runtime013-multiprovider"',
    1
)
gradle.write_text(x)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME013_CHATGPT=RUNTIME012_DEVICE_PASS_PRESERVE\n"
    "PROVIDER_RUNTIME013_GEMINI=GOLDEN_COMPOSER_PLUS_MANUAL_CONFIRM_EXECUTION_GUARD\n"
    "PROVIDER_RUNTIME013_CLAUDE=EXISTING_ADAPTER_ENABLED_STRICT_AUTH_REQUIRED\n"
    "PROVIDER_RUNTIME013_GROK=NEW_ANDROID_CANDIDATE_ADAPTER_DEVICE_REPLAY_REQUIRED\n"
    "PROVIDER_RUNTIME013_O24=UNCHANGED_SERVER_AUTH_TRUE_STOP_UNAUTHORIZED\n"
    "PROVIDER_RUNTIME013_NO_GOLDEN_CLAIM_FOR_CLAUDE_OR_GROK_ANDROID=true\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Static invariants.
main = main_path.read_text()
gemini = gemini_path.read_text()
claude = claude_path.read_text()
grok = (assets / "grok_provider_013.js").read_text()
transport = transport_path.read_text()
origin = origin_path.read_text()
bridge = bridge_path.read_text()

for token in [
    'SelectedProvider.CLAUDE -> CLAUDE_RUNTIME_CHANNEL',
    'SelectedProvider.GROK -> GROK_CHANNEL',
    '"ANTHROPIC" -> "Anthropic"',
    '"XAI" -> "xAI"',
    '.put("user_confirmed_connected", providerConfirmedByUser)',
]:
    assert token in main, token
assert "manuallyConfirmed&&!!composerAtDispatch" in gemini
assert "type:'BRIDGE_READY'" in claude
assert "NEXUS_V007_GROK_013" in grok
assert "SelectedProvider.GROK" in transport
assert '"https://grok.com"' in origin
assert "grokAdapterScript" in bridge
