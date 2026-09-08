from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Start strictly from the validated UIRETRY1 derivative. This preserves the
# ChatGPT path and the exact auth-origin policy before Claude-only controller
# changes are applied.
subprocess.run(
    ["python3", str(repo / "executionproof006_uiretry1" / "derive.py"), str(repo), str(work)],
    check=True,
)

# Side-by-side package/version/label for the Claude proof derivative.
p = work / "app/build.gradle.kts"
g = p.read_text()
old_app = 'applicationId = "nexus.android.c002.executionproof006.uiretry1"'
old_ver_code = 'versionCode = 10'
old_ver_name = 'versionName = "0.0.10-c002-executionproof006-uiretry1"'
assert g.count(old_app) == 1, "applicationId baseline mismatch"
assert g.count(old_ver_code) == 1, "versionCode baseline mismatch"
assert g.count(old_ver_name) == 1, "versionName baseline mismatch"
g = g.replace(old_app, 'applicationId = "nexus.android.c002.claudeexecutionproof010"')
g = g.replace(old_ver_code, 'versionCode = 11')
g = g.replace(old_ver_name, 'versionName = "0.0.11-c002-claude-executionproof010"')
p.write_text(g)

p = work / "app/src/main/AndroidManifest.xml"
m = p.read_text()
old_label = 'android:label="NEXUS C002 EXECUTION PROOF 006 UIRETRY1"'
assert m.count(old_label) == 1, "manifest UIRETRY1 label mismatch"
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE EXECUTION PROOF 010"'))

main = work / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main.read_text()

old_profile = 'nexus_provider_profile_c002_executionproof006_uiretry1'
assert s.count(old_profile) == 1, "profile mismatch"
s = s.replace(old_profile, 'nexus_provider_profile_c002_claude_executionproof010')

needle = '    private var lastAuthState: String? = null\n'
assert s.count(needle) == 1, "lastAuthState anchor mismatch"
s = s.replace(needle, needle + '    private var providerChannel: String? = null\n')

old_handler = '''        renderStatus()
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
'''
new_handler = '''        renderStatus()
        webView.loadUrl("$CLAUDE_ORIGIN/")
    }

    private fun handleBridgeMessage(origin: String, payload: String) {
        if (proofStopped) return
        val normalizedOrigin = origin.trimEnd('/')
        if (normalizedOrigin != CLAUDE_ORIGIN) {
            block("ANDROID_BRIDGE_ORIGIN_MISMATCH")
            return
        }
        val message = runCatching { JSONObject(payload) }.getOrElse {
            block("ANDROID_BRIDGE_MESSAGE_MALFORMED")
            return
        }
        val type = message.optString("type")
        val channel = message.optString("channel")
        val boundChannel = providerChannel
        if (boundChannel == null) {
            if (!type.endsWith("_STATUS") || channel.isBlank()) {
                block("ANDROID_BRIDGE_CHANNEL_UNBOUND")
                return
            }
            providerChannel = channel
            recordDiagnostic("CLAUDE_CHANNEL_BOUND", normalizedOrigin, "status_type=$type")
        } else if (channel != boundChannel) {
            block("ANDROID_BRIDGE_CHANNEL_MISMATCH")
            return
        }

        when {
            type.endsWith("_STATUS") -> handleStatus(normalizedOrigin, message)
            type == "PROVIDER_ACK" -> handleProviderAck(message)
            type == "PROVIDER_PROGRESS" -> handleProviderProgress(message)
            type == "PROVIDER_RESULT" -> handleProviderResult(normalizedOrigin, message)
        }
    }
'''
assert s.count(old_handler) == 1, "bridge handler anchor mismatch"
s = s.replace(old_handler, new_handler)

# Claude descriptor/origin + unique provider selection.
assert s.count('RuntimeGate.validateDescriptor(descriptor, CHATGPT_ORIGIN)') == 1
s = s.replace('RuntimeGate.validateDescriptor(descriptor, CHATGPT_ORIGIN)', 'RuntimeGate.validateDescriptor(descriptor, CLAUDE_ORIGIN)')
assert s.count('provider = SelectedProvider.CHATGPT,') == 1
s = s.replace('provider = SelectedProvider.CHATGPT,', 'provider = SelectedProvider.CLAUDE,')
assert s.count('.put("provider", "OpenAI")') == 1
s = s.replace('.put("provider", "OpenAI")', '.put("provider", "Anthropic")')

old_outbound = '''        val outbound = JSONObject()
            .put("channel", CHATGPT_CHANNEL)
            .put("type", "EXECUTE_JOB")
            .put("bridge_run_id", BRIDGE_RUN_ID)
            .put("envelope", envelope)
'''
new_outbound = '''        val channel = providerChannel
        if (channel.isNullOrBlank()) {
            block("ANDROID_BRIDGE_CHANNEL_UNBOUND")
            return
        }
        val outbound = JSONObject()
            .put("channel", channel)
            .put("type", "EXECUTE_JOB")
            .put("bridge_run_id", BRIDGE_RUN_ID)
            .put("envelope", envelope)
'''
assert s.count(old_outbound) == 1, "outbound channel anchor mismatch"
s = s.replace(old_outbound, new_outbound)

for before, after in [
    ('recordDiagnostic("ACK_PASS", CHATGPT_ORIGIN,', 'recordDiagnostic("ACK_PASS", CLAUDE_ORIGIN,'),
    ('currentHeadline = "ACK PASS — provider polling ChatGPT UI"', 'currentHeadline = "ACK PASS — provider polling Claude UI"'),
    ('recordDiagnostic("PROVIDER_PROGRESS", CHATGPT_ORIGIN,', 'recordDiagnostic("PROVIDER_PROGRESS", CLAUDE_ORIGIN,'),
    ('if (uiOrigin != CHATGPT_ORIGIN)', 'if (uiOrigin != CLAUDE_ORIGIN)'),
    ('.put("contract", "V005-C002-EXECUTION-PROOF-006")', '.put("contract", "V005-C002-CLAUDE-EXECUTION-PROOF-010")'),
    ('if (model.optString("provider") != "OpenAI")', 'if (model.optString("provider") != "Anthropic")'),
]:
    assert s.count(before) == 1, f"anchor mismatch: {before}"
    s = s.replace(before, after)

replacements = [
    ('const val CHATGPT_ORIGIN = "https://chatgpt.com"', 'const val CLAUDE_ORIGIN = "https://claude.ai"'),
    ('        const val CHATGPT_CHANNEL = "NEXUS_POC022_C8B2R1"\n', ''),
    ('const val BRIDGE_RUN_ID = "V005-C002-EXECUTION-PROOF-006-BRIDGE-001"', 'const val BRIDGE_RUN_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-BRIDGE-001"'),
    ('const val JOB_ID = "V005-C002-EXECUTION-PROOF-006-001"', 'const val JOB_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-001"'),
    ('const val COMPARISON_ID = "V005-C002-EXECUTION-PROOF-006-COMP-001"', 'const val COMPARISON_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-COMP-001"'),
    ('const val RESULT_PACK_VERSION = "V005_EXECUTION_PROOF_006_V1"', 'const val RESULT_PACK_VERSION = "V005_CLAUDE_EXECUTION_PROOF_010_V1"'),
    ('const val PROOF_TOKEN = "NEXUS_EXECUTION_PROOF_006_OK"', 'const val PROOF_TOKEN = "NEXUS_CLAUDE_EXECUTION_PROOF_010_OK"'),
    ('const val MODEL_REF = "ChatGPT UI session — exact backend model not exposed by bridge"', 'const val MODEL_REF = "Claude UI session — exact backend model not exposed by bridge"'),
    ('const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android transport proof. The answer field must be NEXUS_EXECUTION_PROOF_006_OK."', 'const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android Claude transport proof. The answer field must be NEXUS_CLAUDE_EXECUTION_PROOF_010_OK."'),
    ('const val PROOF_HANDOFF = "Read-only V-005 Android execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."', 'const val PROOF_HANDOFF = "Read-only V-005 Android Claude execution proof. Use only the frozen package. No web research, no canonical write, no state mutation."'),
    ('const val ACTIVE_HEADLINE = "EXECUTION PROOF 006 — authenticate in ChatGPT; one read-only proof job will run after DESCRIBE PASS"', 'const val ACTIVE_HEADLINE = "CLAUDE EXECUTION PROOF 010 — authenticate in Claude; one read-only proof job will run after DESCRIBE PASS"'),
]
for before, after in replacements:
    assert s.count(before) == 1, f"replacement anchor mismatch: {before}"
    s = s.replace(before, after)

# Preserve the protocol constant that the validated C002 engine already uses.
assert 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' in s

# Fail closed if any ChatGPT-specific controller routing survived.
assert 'SelectedProvider.CHATGPT' not in s
assert 'CHATGPT_ORIGIN' not in s
assert 'CHATGPT_CHANNEL' not in s
assert 'SelectedProvider.CLAUDE' in s
assert 'CLAUDE_ORIGIN = "https://claude.ai"' in s
assert '.put("provider", "Anthropic")' in s
assert 'model.optString("provider") != "Anthropic"' in s

main.write_text(s)
