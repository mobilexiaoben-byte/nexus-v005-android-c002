from pathlib import Path
import shutil
import subprocess
import sys

repo=Path(sys.argv[1]).resolve()
work=Path(sys.argv[2]).resolve()

# Start from the validated Gemini Android proof derivative so the proven
# WebView hardening/auth-host chain and 3-provider bridge remain intact.
subprocess.run(['python3',str(repo/'geminiproof001'/'derive.py'),str(repo),str(work)],check=True)

# Add the Z.ai provider asset; existing ChatGPT/Claude/Gemini adapters are preserved.
shutil.copy2(repo/'zaiproof001'/'zai_provider_c002.js',work/'app/src/main/assets/nexus/zai_provider_c002.js')

# Independent package/version/label.
p=work/'app/build.gradle.kts'; s=p.read_text()
repls=[
('applicationId = "nexus.android.c002.geminiexecutionproof001"','applicationId = "nexus.android.c002.zaiexecutionproof001"'),
('versionCode = 27','versionCode = 28'),
('versionName = "0.0.27-v004-gemini-android-proof001"','versionName = "0.0.28-v005-zai-android-proof001"')]
for a,b in repls:
    assert s.count(a)==1,a; s=s.replace(a,b)
p.write_text(s)

p=work/'app/src/main/AndroidManifest.xml'; s=p.read_text()
a='android:label="NEXUS V004 GEMINI ANDROID PROOF 001"'; assert s.count(a)==1
p.write_text(s.replace(a,'android:label="NEXUS ZAI ANDROID PROOF 001"'))

# Add ZAI as a first-class provider without changing the validated Gemini policy.
p=work/'app/src/main/java/nexus/android/c002/core/TransportContract.kt'; s=p.read_text()
a='enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI }'
b='enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI, ZAI }'
assert s.count(a)==1,'SelectedProvider enum anchor mismatch'; s=s.replace(a,b)
a='        SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true)\n'
b='        SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true),\n        SelectedProvider.ZAI to ProviderPolicy("ZAI", "ADP-ZAI-GLM-FAMILY", "https://chat.z.ai", true)\n'
assert s.count(a)==1,'provider policy anchor mismatch'; s=s.replace(a,b)
p.write_text(s)

# Add Z.ai bridge/top-level origins. Existing bounded Google auth hosts remain intact.
p=work/'app/src/main/java/nexus/android/c002/web/OriginPolicy.kt'; s=p.read_text()
a='''        "https://chatgpt.com",\n        "https://claude.ai",\n        "https://gemini.google.com"\n'''
b='''        "https://chatgpt.com",\n        "https://claude.ai",\n        "https://gemini.google.com",\n        "https://chat.z.ai"\n'''
assert s.count(a)==1,'bridgeOrigins anchor mismatch'; s=s.replace(a,b)
a='''            host == "gemini.google.com" || host.endsWith(".gemini.google.com") ||\n            host == "accounts.google.com" ||\n'''
b='''            host == "gemini.google.com" || host.endsWith(".gemini.google.com") ||\n            host == "z.ai" || host.endsWith(".z.ai") ||\n            host == "accounts.google.com" ||\n'''
assert s.count(a)==1,'Z.ai top-level insertion anchor mismatch'; s=s.replace(a,b)
p.write_text(s)

# Extend isolated bridge installation from 3 providers to 4 providers.
p=work/'app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt'; s=p.read_text()
a='fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String): BridgeInstallResult {'
b='fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String, zaiAdapterScript: String): BridgeInstallResult {'
assert s.count(a)==1,'install signature anchor mismatch'; s=s.replace(a,b)
a='''        WebViewCompat.addJavaScriptOnEvent(\n            webView,\n            geminiAdapterScript,\n            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,\n            setOf("https://gemini.google.com"),\n            isolatedWorld\n        )\n        return BridgeInstallResult(true, "PASS")\n'''
b='''        WebViewCompat.addJavaScriptOnEvent(\n            webView,\n            geminiAdapterScript,\n            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,\n            setOf("https://gemini.google.com"),\n            isolatedWorld\n        )\n        WebViewCompat.addJavaScriptOnEvent(\n            webView,\n            zaiAdapterScript,\n            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,\n            setOf("https://chat.z.ai"),\n            isolatedWorld\n        )\n        return BridgeInstallResult(true, "PASS")\n'''
assert s.count(a)==1,'Gemini injection anchor mismatch'; s=s.replace(a,b)
p.write_text(s)

# Retarget the proven native execution controller from Gemini to Z.ai.
p=work/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=p.read_text()
a='''        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }\n        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }\n        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }\n        bridge = NexusWebBridge(webView, ::handleBridgeMessage)\n        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter)\n'''
b='''        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }\n        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }\n        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }\n        val zaiAdapter = assets.open("nexus/zai_provider_c002.js").bufferedReader().use { it.readText() }\n        bridge = NexusWebBridge(webView, ::handleBridgeMessage)\n        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter, zaiAdapter)\n'''
assert s.count(a)==1,'adapter install anchor mismatch'; s=s.replace(a,b)

pairs=[
('nexus_provider_profile_v004_gemini_proof001','nexus_provider_profile_v005_zai_proof001'),
('webView.loadUrl("$GEMINI_ORIGIN/")','webView.loadUrl("$ZAI_ORIGIN/")'),
('message.optString("channel") != GEMINI_CHANNEL','message.optString("channel") != ZAI_CHANNEL'),
('"GEMINI_STATUS" -> handleStatus(origin, message)','"ZAI_STATUS" -> handleStatus(origin, message)'),
('RuntimeGate.validateDescriptor(descriptor, GEMINI_ORIGIN)','RuntimeGate.validateDescriptor(descriptor, ZAI_ORIGIN)'),
('provider = SelectedProvider.GEMINI,','provider = SelectedProvider.ZAI,'),
('.put("provider", "Google")','.put("provider", "Z.ai")'),
('.put("channel", GEMINI_CHANNEL)','.put("channel", ZAI_CHANNEL)'),
('recordDiagnostic("ACK_PASS", GEMINI_ORIGIN,','recordDiagnostic("ACK_PASS", ZAI_ORIGIN,'),
('currentHeadline = "ACK PASS — provider polling Gemini UI"','currentHeadline = "ACK PASS — provider polling Z.ai UI"'),
('recordDiagnostic("PROVIDER_PROGRESS", GEMINI_ORIGIN,','recordDiagnostic("PROVIDER_PROGRESS", ZAI_ORIGIN,'),
('if (uiOrigin != GEMINI_ORIGIN)','if (uiOrigin != ZAI_ORIGIN)'),
('.put("contract", "V004-GEMINI-ANDROID-PROOF-001")','.put("contract", "V005-ZAI-ANDROID-PROOF-001")'),
('if (model.optString("provider") != "Google")','if (model.optString("provider") != "Z.ai")'),
('const val GEMINI_ORIGIN = "https://gemini.google.com"','const val ZAI_ORIGIN = "https://chat.z.ai"'),
('const val GEMINI_CHANNEL = "NEXUS_V004_GEMINI_001"','const val ZAI_CHANNEL = "NEXUS_V005_ZAI_001"'),
('const val BRIDGE_RUN_ID = "V004-GEMINI-ANDROID-PROOF-001-BRIDGE-001"','const val BRIDGE_RUN_ID = "V005-ZAI-ANDROID-PROOF-001-BRIDGE-001"'),
('const val JOB_ID = "V004-GEMINI-ANDROID-PROOF-001"','const val JOB_ID = "V005-ZAI-ANDROID-PROOF-001"'),
('const val COMPARISON_ID = "V004-GEMINI-ANDROID-PROOF-001-COMP-001"','const val COMPARISON_ID = "V005-ZAI-ANDROID-PROOF-001-COMP-001"'),
('const val RESULT_PACK_VERSION = "V004_GEMINI_ANDROID_PROOF_001_V1"','const val RESULT_PACK_VERSION = "V005_ZAI_ANDROID_PROOF_001_V1"'),
('const val PROOF_TOKEN = "NEXUS_GEMINI_EXECUTION_PROOF_001_OK"','const val PROOF_TOKEN = "NEXUS_ZAI_EXECUTION_PROOF_001_OK"'),
('const val MODEL_REF = "Gemini UI session — exact backend model not exposed by bridge"','const val MODEL_REF = "Z.ai UI session — exact backend model not exposed by bridge"'),
('const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android Gemini transport proof. The answer field must be NEXUS_GEMINI_EXECUTION_PROOF_001_OK."','const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android Z.ai transport proof. The answer field must be NEXUS_ZAI_EXECUTION_PROOF_001_OK."'),
('const val PROOF_HANDOFF = "Read-only V-004 Gemini Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."','const val PROOF_HANDOFF = "Read-only V-005 Z.ai Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."'),
('const val ACTIVE_HEADLINE = "GEMINI PROOF 001 — authenticate in Gemini; one read-only proof job will run after DESCRIBE PASS"','const val ACTIVE_HEADLINE = "Z.AI PROOF 001 — sign in or use a ready session; one read-only proof job will run after DESCRIBE PASS"')]
for a,b in pairs:
    assert s.count(a)==1,f'anchor mismatch: {a}'
    s=s.replace(a,b)

assert 'SelectedProvider.ZAI' in s
assert 'ZAI_ORIGIN = "https://chat.z.ai"' in s
assert '.put("provider", "Z.ai")' in s
assert 'model.optString("provider") != "Z.ai"' in s
assert 'GEMINI_ORIGIN' not in s
assert 'GEMINI_CHANNEL' not in s
p.write_text(s)
