from pathlib import Path
import shutil
import subprocess
import sys

repo=Path(sys.argv[1]).resolve()
work=Path(sys.argv[2]).resolve()

# Start strictly from the validated ChatGPT UIRETRY1 Android proof baseline.
subprocess.run(['python3',str(repo/'executionproof006_uiretry1'/'derive.py'),str(repo),str(work)],check=True)

# Add the Gemini provider asset without modifying ChatGPT/Claude adapter sources.
shutil.copy2(repo/'geminiproof001'/'gemini_provider_c002.js',work/'app/src/main/assets/nexus/gemini_provider_c002.js')

# Independent package/version/label.
p=work/'app/build.gradle.kts'; s=p.read_text()
repls=[
('applicationId = "nexus.android.c002.executionproof006.uiretry1"','applicationId = "nexus.android.c002.geminiexecutionproof001"'),
('versionCode = 10','versionCode = 27'),
('versionName = "0.0.10-c002-executionproof006-uiretry1"','versionName = "0.0.27-v004-gemini-android-proof001"')]
for a,b in repls:
    assert s.count(a)==1,a; s=s.replace(a,b)
p.write_text(s)

p=work/'app/src/main/AndroidManifest.xml'; s=p.read_text()
a='android:label="NEXUS C002 EXECUTION PROOF 006 UIRETRY1"'; assert s.count(a)==1
p.write_text(s.replace(a,'android:label="NEXUS V004 GEMINI ANDROID PROOF 001"'))

# V-004 is the authority that enables the already-declared Gemini provider policy.
p=work/'app/src/main/java/nexus/android/c002/core/TransportContract.kt'; s=p.read_text()
a='SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", false)'
b='SelectedProvider.GEMINI to ProviderPolicy("GOOGLE", "ADP-GOOGLE-FAMILY", "https://gemini.google.com", true)'
assert s.count(a)==1,'Gemini disabled policy anchor mismatch'
p.write_text(s.replace(a,b))

# Bridge origin + top-level Gemini origin. Existing bounded Google auth hosts from UIRETRY1 remain intact.
p=work/'app/src/main/java/nexus/android/c002/web/OriginPolicy.kt'; s=p.read_text()
a='''        "https://chatgpt.com",\n        "https://claude.ai"\n'''
b='''        "https://chatgpt.com",\n        "https://claude.ai",\n        "https://gemini.google.com"\n'''
assert s.count(a)==1,'bridgeOrigins anchor mismatch'; s=s.replace(a,b)
a='''            host == "claude.ai" || host.endsWith(".claude.ai") ||\n            host == "anthropic.com" || host.endsWith(".anthropic.com") ||\n'''
b='''            host == "claude.ai" || host.endsWith(".claude.ai") ||\n            host == "anthropic.com" || host.endsWith(".anthropic.com") ||\n            host == "gemini.google.com" || host.endsWith(".gemini.google.com") ||\n'''
assert s.count(a)==1,'top-level Gemini insertion anchor mismatch'; s=s.replace(a,b)
p.write_text(s)

# Extend isolated bridge installation from 2 providers to 3 providers.
p=work/'app/src/main/java/nexus/android/c002/web/NexusWebBridge.kt'; s=p.read_text()
a='fun install(chatGptAdapterScript: String, claudeAdapterScript: String): BridgeInstallResult {'
b='fun install(chatGptAdapterScript: String, claudeAdapterScript: String, geminiAdapterScript: String): BridgeInstallResult {'
assert s.count(a)==1,'install signature anchor mismatch'; s=s.replace(a,b)
a='''        WebViewCompat.addJavaScriptOnEvent(\n            webView,\n            claudeAdapterScript,\n            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,\n            setOf("https://claude.ai"),\n            isolatedWorld\n        )\n        return BridgeInstallResult(true, "PASS")\n'''
b='''        WebViewCompat.addJavaScriptOnEvent(\n            webView,\n            claudeAdapterScript,\n            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,\n            setOf("https://claude.ai"),\n            isolatedWorld\n        )\n        WebViewCompat.addJavaScriptOnEvent(\n            webView,\n            geminiAdapterScript,\n            WebViewCompat.INJECTION_EVENT_DOCUMENT_START,\n            setOf("https://gemini.google.com"),\n            isolatedWorld\n        )\n        return BridgeInstallResult(true, "PASS")\n'''
assert s.count(a)==1,'Claude injection anchor mismatch'; s=s.replace(a,b)
p.write_text(s)

# Retarget the proven native execution controller to Gemini.
p=work/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=p.read_text()
a='''        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }\n        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }\n        bridge = NexusWebBridge(webView, ::handleBridgeMessage)\n        val install = bridge!!.install(chatGptAdapter, claudeAdapter)\n'''
b='''        val chatGptAdapter = assets.open("nexus/chatgpt_provider_c002.js").bufferedReader().use { it.readText() }\n        val claudeAdapter = assets.open("nexus/claude_provider_c002.js").bufferedReader().use { it.readText() }\n        val geminiAdapter = assets.open("nexus/gemini_provider_c002.js").bufferedReader().use { it.readText() }\n        bridge = NexusWebBridge(webView, ::handleBridgeMessage)\n        val install = bridge!!.install(chatGptAdapter, claudeAdapter, geminiAdapter)\n'''
assert s.count(a)==1,'adapter install anchor mismatch'; s=s.replace(a,b)

pairs=[
('nexus_provider_profile_c002_executionproof006_uiretry1','nexus_provider_profile_v004_gemini_proof001'),
('webView.loadUrl("$CHATGPT_ORIGIN/")','webView.loadUrl("$GEMINI_ORIGIN/")'),
('message.optString("channel") != CHATGPT_CHANNEL','message.optString("channel") != GEMINI_CHANNEL'),
('"CHATGPT_STATUS" -> handleStatus(origin, message)','"GEMINI_STATUS" -> handleStatus(origin, message)'),
('RuntimeGate.validateDescriptor(descriptor, CHATGPT_ORIGIN)','RuntimeGate.validateDescriptor(descriptor, GEMINI_ORIGIN)'),
('provider = SelectedProvider.CHATGPT,','provider = SelectedProvider.GEMINI,'),
('.put("provider", "OpenAI")','.put("provider", "Google")'),
('.put("channel", CHATGPT_CHANNEL)','.put("channel", GEMINI_CHANNEL)'),
('recordDiagnostic("ACK_PASS", CHATGPT_ORIGIN,','recordDiagnostic("ACK_PASS", GEMINI_ORIGIN,'),
('currentHeadline = "ACK PASS — provider polling ChatGPT UI"','currentHeadline = "ACK PASS — provider polling Gemini UI"'),
('recordDiagnostic("PROVIDER_PROGRESS", CHATGPT_ORIGIN,','recordDiagnostic("PROVIDER_PROGRESS", GEMINI_ORIGIN,'),
('if (uiOrigin != CHATGPT_ORIGIN)','if (uiOrigin != GEMINI_ORIGIN)'),
('.put("contract", "V005-C002-EXECUTION-PROOF-006")','.put("contract", "V004-GEMINI-ANDROID-PROOF-001")'),
('if (model.optString("provider") != "OpenAI")','if (model.optString("provider") != "Google")'),
('const val CHATGPT_ORIGIN = "https://chatgpt.com"','const val GEMINI_ORIGIN = "https://gemini.google.com"'),
('const val CHATGPT_CHANNEL = "NEXUS_POC022_C8B2R1"','const val GEMINI_CHANNEL = "NEXUS_V004_GEMINI_001"'),
('const val BRIDGE_RUN_ID = "V005-C002-EXECUTION-PROOF-006-BRIDGE-001"','const val BRIDGE_RUN_ID = "V004-GEMINI-ANDROID-PROOF-001-BRIDGE-001"'),
('const val JOB_ID = "V005-C002-EXECUTION-PROOF-006-001"','const val JOB_ID = "V004-GEMINI-ANDROID-PROOF-001"'),
('const val COMPARISON_ID = "V005-C002-EXECUTION-PROOF-006-COMP-001"','const val COMPARISON_ID = "V004-GEMINI-ANDROID-PROOF-001-COMP-001"'),
('const val RESULT_PACK_VERSION = "V005_EXECUTION_PROOF_006_V1"','const val RESULT_PACK_VERSION = "V004_GEMINI_ANDROID_PROOF_001_V1"'),
('const val PROOF_TOKEN = "NEXUS_EXECUTION_PROOF_006_OK"','const val PROOF_TOKEN = "NEXUS_GEMINI_EXECUTION_PROOF_001_OK"'),
('const val MODEL_REF = "ChatGPT UI session — exact backend model not exposed by bridge"','const val MODEL_REF = "Gemini UI session — exact backend model not exposed by bridge"'),
('const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android transport proof. The answer field must be NEXUS_EXECUTION_PROOF_006_OK."','const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android Gemini transport proof. The answer field must be NEXUS_GEMINI_EXECUTION_PROOF_001_OK."'),
('const val PROOF_HANDOFF = "Read-only V-005 Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."','const val PROOF_HANDOFF = "Read-only V-004 Gemini Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."'),
('const val ACTIVE_HEADLINE = "EXECUTION PROOF 006 — authenticate in ChatGPT; one read-only proof job will run after DESCRIBE PASS"','const val ACTIVE_HEADLINE = "GEMINI PROOF 001 — authenticate in Gemini; one read-only proof job will run after DESCRIBE PASS"')]
for a,b in pairs:
    assert s.count(a)==1,f'anchor mismatch: {a}'
    s=s.replace(a,b)

# Fail closed against controller routing leftovers.
assert 'SelectedProvider.CHATGPT' not in s
assert 'CHATGPT_ORIGIN' not in s
assert 'CHATGPT_CHANNEL' not in s
assert 'SelectedProvider.GEMINI' in s
assert 'GEMINI_ORIGIN = "https://gemini.google.com"' in s
assert '.put("provider", "Google")' in s
assert 'model.optString("provider") != "Google"' in s
p.write_text(s)
