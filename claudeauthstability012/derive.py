from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
work = Path(sys.argv[2]).resolve()

# Rebuild strictly from Claude010. Provider selectors/assets remain byte-identical.
subprocess.run([
    'python3', str(repo / 'executionproof010_claude' / 'derive.py'), str(repo), str(work)
], check=True)

# Side-by-side identity.
p = work / 'app/build.gradle.kts'
g = p.read_text()
for before, after in [
    ('applicationId = "nexus.android.c002.claudeexecutionproof010"', 'applicationId = "nexus.android.c002.claudeauthstability012"'),
    ('versionCode = 11', 'versionCode = 13'),
    ('versionName = "0.0.11-c002-claude-executionproof010"', 'versionName = "0.0.13-c002-claude-authstability012"'),
]:
    assert g.count(before) == 1, f'gradle anchor mismatch: {before}'
    g = g.replace(before, after)
p.write_text(g)

p = work / 'app/src/main/AndroidManifest.xml'
m = p.read_text()
old_label = 'android:label="NEXUS C002 CLAUDE EXECUTION PROOF 010"'
assert m.count(old_label) == 1, 'manifest label mismatch'
p.write_text(m.replace(old_label, 'android:label="NEXUS C002 CLAUDE AUTH STABILITY 012"'))

main = work / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()

# Identity + controller-only state.
for before, after in [
    ('nexus_provider_profile_c002_claude_executionproof010', 'nexus_provider_profile_c002_claude_authstability012'),
    ('    private var providerChannel: String? = null\n',
     '    private var providerChannel: String? = null\n'
     '    private var authenticatedStableSinceMs: Long? = null\n'
     '    private var authenticatedStableCount = 0\n'
     '    private var authenticatedStableReason: String? = null\n'),
    ('                    lastAuthState = null\n',
     '                    lastAuthState = null\n'
     '                    authenticatedStableSinceMs = null\n'
     '                    authenticatedStableCount = 0\n'
     '                    authenticatedStableReason = null\n'),
]:
    assert s.count(before) == 1, f'main anchor mismatch: {before}'
    s = s.replace(before, after)

old_window = '''            override fun onCreateWindow(
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
'''
new_window = '''            override fun onCreateWindow(
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
                // Always deny auxiliary windows. Before execution this is non-terminal so
                // Claude's progressive UI/auth hydration can continue in the main frame.
                // During a real execution, preserve the original fail-closed stop.
                if (executionStarted && !terminalReceived) {
                    block("EXECUTION_NEW_WINDOW_REQUESTED")
                } else {
                    recordDiagnostic(
                        event = "onCreateWindowDeniedPreExecution",
                        rawUrl = view?.url,
                        detail = "non_terminal=true;dialog=$isDialog;user_gesture=$isUserGesture"
                    )
                }
                return false
            }
'''
assert s.count(old_window) == 1, 'onCreateWindow anchor mismatch'
s = s.replace(old_window, new_window)

old_handle = '''    private fun handleStatus(origin: String, message: JSONObject) {
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
        val gate = RuntimeGate.validateDescriptor(descriptor, CLAUDE_ORIGIN)
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
'''
new_handle = '''    private fun handleStatus(origin: String, message: JSONObject) {
        if (executionStarted || describePassed || proofStopped) return
        val auth = message.optJSONObject("status") ?: run {
            block("ANDROID_DESCRIBE_STATUS_MISSING")
            return
        }
        val authState = auth.optString("state", "UNKNOWN")
        val authReason = auth.optString("reason", "NO_REASON")
        val observedAtMs = auth.optLong("observed_at_ms", 0L).takeIf { it > 0L }
            ?: System.currentTimeMillis()
        val authChanged = authState != lastAuthState
        if (authChanged) {
            lastAuthState = authState
            recordDiagnostic("bridgeStatus", origin, "auth_state=$authState;reason=${sanitizeCode(authReason)}")
        }

        when (authState) {
            "UNKNOWN" -> {
                authenticatedStableSinceMs = null
                authenticatedStableCount = 0
                authenticatedStableReason = null
                if (authChanged || currentHeadline != AUTH_STABILIZING_HEADLINE) {
                    currentHeadline = AUTH_STABILIZING_HEADLINE
                    currentBody = null
                    renderStatus()
                }
                return
            }
            "UNAUTHENTICATED" -> {
                authenticatedStableSinceMs = null
                authenticatedStableCount = 0
                authenticatedStableReason = null
                if (authChanged || currentHeadline != AUTH_REQUIRED_HEADLINE) {
                    currentHeadline = AUTH_REQUIRED_HEADLINE
                    currentBody = null
                    renderStatus()
                }
                return
            }
            "AUTHENTICATED" -> {
                if (authenticatedStableSinceMs == null || authenticatedStableReason != authReason) {
                    authenticatedStableSinceMs = observedAtMs
                    authenticatedStableCount = 1
                    authenticatedStableReason = authReason
                    recordDiagnostic(
                        "AUTH_STABILITY_WAIT",
                        origin,
                        "count=1;reason=${sanitizeCode(authReason)}"
                    )
                    currentHeadline = AUTH_STABILIZING_HEADLINE
                    currentBody = null
                    renderStatus()
                    return
                }

                authenticatedStableCount += 1
                val stableMs = (observedAtMs - (authenticatedStableSinceMs ?: observedAtMs)).coerceAtLeast(0L)
                if (authenticatedStableCount < CLAUDE_AUTH_STABLE_MIN_OBSERVATIONS || stableMs < CLAUDE_AUTH_STABLE_MIN_MS) {
                    if (authenticatedStableCount == 2) {
                        recordDiagnostic(
                            "AUTH_STABILITY_WAIT",
                            origin,
                            "count=$authenticatedStableCount;stable_ms=$stableMs"
                        )
                    }
                    return
                }

                recordDiagnostic(
                    "AUTH_STABILITY_PASS",
                    origin,
                    "count=$authenticatedStableCount;stable_ms=$stableMs;reason=${sanitizeCode(authReason)}"
                )
            }
            else -> {
                block("ANDROID_AUTH_STATE_INVALID:${sanitizeCode(authState)}")
                return
            }
        }

        val descriptor = BridgeDescriptor(
            authenticated = true,
            origin = origin,
            targetCount = 1,
            adapterReady = true,
            missingFeatures = emptySet()
        )
        val gate = RuntimeGate.validateDescriptor(descriptor, CLAUDE_ORIGIN)
        if (!gate.pass) {
            block("DESCRIBE_${gate.code}")
            return
        }

        describePassed = true
        recordDiagnostic("DESCRIBE_PASS", origin, "authenticated=true;stable=true")
        currentHeadline = "DESCRIBE PASS — stable Claude auth — execution proof starting"
        currentBody = null
        renderStatus()
        startExecutionProof(origin)
    }
'''
assert s.count(old_handle) == 1, 'handleStatus anchor mismatch'
s = s.replace(old_handle, new_handle)

for before, after in [
    ('const val BRIDGE_RUN_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-BRIDGE-001"', 'const val BRIDGE_RUN_ID = "V005-C002-CLAUDE-AUTH-STABILITY-012-BRIDGE-001"'),
    ('const val JOB_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-001"', 'const val JOB_ID = "V005-C002-CLAUDE-AUTH-STABILITY-012-001"'),
    ('const val COMPARISON_ID = "V005-C002-CLAUDE-EXECUTION-PROOF-010-COMP-001"', 'const val COMPARISON_ID = "V005-C002-CLAUDE-AUTH-STABILITY-012-COMP-001"'),
    ('const val RESULT_PACK_VERSION = "V005_CLAUDE_EXECUTION_PROOF_010_V1"', 'const val RESULT_PACK_VERSION = "V005_CLAUDE_AUTH_STABILITY_012_V1"'),
    ('const val PROOF_TOKEN = "NEXUS_CLAUDE_EXECUTION_PROOF_010_OK"', 'const val PROOF_TOKEN = "NEXUS_CLAUDE_AUTH_STABILITY_012_OK"'),
    ('const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android Claude transport proof. The answer field must be NEXUS_CLAUDE_EXECUTION_PROOF_010_OK."', 'const val PROOF_QUESTION = "Return the exact frozen Result Pack for this Android Claude auth-stability transport proof. The answer field must be NEXUS_CLAUDE_AUTH_STABILITY_012_OK."'),
    ('const val ACTIVE_HEADLINE = "CLAUDE EXECUTION PROOF 010 — authenticate in Claude; one read-only proof job will run after DESCRIBE PASS"', 'const val ACTIVE_HEADLINE = "CLAUDE AUTH STABILITY 012 — waiting for stable authenticated Claude before DESCRIBE"'),
    ('const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; execution starts only after authenticated DESCRIBE PASS"', 'const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; transient unauthenticated states are non-terminal"'),
    ('.put("contract", "V005-C002-CLAUDE-EXECUTION-PROOF-010")', '.put("contract", "V005-C002-CLAUDE-AUTH-STABILITY-012")'),
]:
    assert s.count(before) == 1, f'constant/content anchor mismatch: {before}'
    s = s.replace(before, after)

anchor = '        const val AUTH_REQUIRED_HEADLINE = "AUTH REQUIRED — sign in below; transient unauthenticated states are non-terminal"\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor +
    '        const val AUTH_STABILIZING_HEADLINE = "CLAUDE AUTH SIGNAL STABILIZING — no DESCRIBE or dispatch yet"\n'
    '        const val CLAUDE_AUTH_STABLE_MIN_OBSERVATIONS = 2\n'
    '        const val CLAUDE_AUTH_STABLE_MIN_MS = 1_500L\n')

# Explicit controller-only invariants.
assert 'CLAUDE_AUTH_STABLE_MIN_MS = 1_500L' in s
assert 'AUTH_STABILITY_PASS' in s
assert 'startExecutionProof(origin)' in s
assert 'if (executionStarted && !terminalReceived)' in s
main.write_text(s)
