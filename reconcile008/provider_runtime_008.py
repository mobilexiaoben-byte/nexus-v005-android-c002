from pathlib import Path
import subprocess
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

subprocess.run([
    sys.executable,
    str(repo / "reconcile007" / "execution_tokenless.py"),
    str(repo),
    str(root),
], check=True)

p = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = p.read_text()

# 008 — main-frame HTTP/WebView errors are navigation diagnostics, not terminal
# provider-execution receipts. The provider adapter remains authoritative and will
# fail closed itself if it cannot execute / return a correlated Result Pack.
old = '                if (request.isForMainFrame && executionStarted && !terminalReceived) block("EXECUTION_MAIN_FRAME_WEB_ERROR_${error.errorCode}")\n'
new = '''                if (request.isForMainFrame && executionStarted && !terminalReceived) {
                    recordDiagnostic("EXECUTION_MAIN_FRAME_WEB_ERROR_NON_TERMINAL", request.url.toString(), "code=${error.errorCode}")
                }
'''
assert old in s, "web error gate anchor missing"
s = s.replace(old, new, 1)

old = '                if (request.isForMainFrame && statusCode >= 400 && executionStarted && !terminalReceived) block("EXECUTION_MAIN_FRAME_HTTP_$statusCode")\n'
new = '''                if (request.isForMainFrame && statusCode >= 400 && executionStarted && !terminalReceived) {
                    recordDiagnostic("EXECUTION_MAIN_FRAME_HTTP_NON_TERMINAL", request.url.toString(), "status=$statusCode")
                }
'''
assert old in s, "http error gate anchor missing"
s = s.replace(old, new, 1)

# Reset stale terminal/block state for every provider switch and every explicit
# user execution attempt. This prevents a previous provider's BLOCKED state from
# poisoning a new provider run.
anchor = '    private fun selectProviderManually(provider: String, origin: String) {\n'
reset = '''    private fun resetExecutionAttempt(reason: String) {
        executionStarted = false
        proofStopped = false
        terminalReceived = false
        productRunRequested = false
        currentBody = null
        recordDiagnostic("EXECUTION_STATE_RESET", selectedProviderOrigin ?: "", reason)
    }

'''
assert anchor in s, "provider method anchor missing"
s = s.replace(anchor, reset + anchor, 1)

old = '''    private fun selectProviderManually(provider: String, origin: String) {
        selectedProvider = provider
        selectedProviderOrigin = origin
        providerConfirmedByUser = false
        productRunRequested = false
'''
new = '''    private fun selectProviderManually(provider: String, origin: String) {
        selectedProvider = provider
        selectedProviderOrigin = origin
        resetExecutionAttempt("PROVIDER_SWITCH:$provider")
        providerConfirmedByUser = false
'''
assert old in s, "provider switch reset anchor missing"
s = s.replace(old, new, 1)

old = '''            productRunRequested = true
            activeUserQuestion = userQuestion
'''
new = '''            resetExecutionAttempt("ANALYSE_NEW_ATTEMPT")
            productRunRequested = true
            activeUserQuestion = userQuestion
'''
assert old in s, "analyse reset anchor missing"
s = s.replace(old, new, 1)

# Fact Check remains tokenless for the user. Reuse an app-private credential if
# one exists; otherwise submit the bounded O24 capture without a client token and
# let the server-side deployment enforce its own authorization policy.
old = '''    private fun startO24CaptureUsingInternalCredential(rawClaim: String) {
        val prefs = getSharedPreferences(O24_PREFS, MODE_PRIVATE)
        val token = prefs.getString(O24_TOKEN_KEY, "").orEmpty().trim()
        if (token.isBlank()) {
            productState.text = "Fact Check · autorisation interne indisponible"
            recordDiagnostic("O24_INTERNAL_CREDENTIAL_MISSING", O24_BRIDGE_URL, "NO_USER_TOKEN_PROMPT")
            return
        }
        startO24Capture(rawClaim, token)
    }

'''
new = '''    private fun startO24CaptureUsingInternalCredential(rawClaim: String) {
        val prefs = getSharedPreferences(O24_PREFS, MODE_PRIVATE)
        val token = prefs.getString(O24_TOKEN_KEY, "").orEmpty().trim()
        if (token.isBlank()) {
            recordDiagnostic("O24_CLIENT_CREDENTIAL_ABSENT", O24_BRIDGE_URL, "TRY_SERVER_SIDE_AUTH_NO_USER_PROMPT")
        }
        startO24Capture(rawClaim, token)
    }

'''
assert old in s, "Fact Check internal credential method missing"
s = s.replace(old, new, 1)

old = '''                val payload = org.json.JSONObject()
                    .put("token", token)
                    .put("operation", "capture")
                    .put("job_id", jobId)
                    .put("raw_claim", rawClaim)
'''
new = '''                val payload = org.json.JSONObject()
                    .put("operation", "capture")
                    .put("job_id", jobId)
                    .put("raw_claim", rawClaim)
                if (token.isNotBlank()) payload.put("token", token)
'''
assert old in s, "Fact Check payload anchor missing"
s = s.replace(old, new, 1)

# Candidate identity; keep applicationId stable so provider sessions and any
# app-private credential survive upgrade from 006/007.
p.write_text(s)

p = root / "app/build.gradle.kts"
g = p.read_text()
assert 'versionCode = 61' in g
assert 'versionName = "0.0.61-v007-m024-u013-execution-tokenless007"' in g
g = g.replace('versionCode = 61', 'versionCode = 62', 1)
g = g.replace(
    'versionName = "0.0.61-v007-m024-u013-execution-tokenless007"',
    'versionName = "0.0.62-v007-m024-u013-provider-runtime008"',
    1
)
p.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
base = lock.read_text()
lock.write_text(base +
    'EXECUTION008_MAIN_FRAME_HTTP=DIAGNOSTIC_NON_TERMINAL\n'
    'EXECUTION008_PROVIDER_ADAPTER=AUTHORITATIVE_TERMINAL_SIGNAL\n'
    'EXECUTION008_STATE_RESET=ON_PROVIDER_SWITCH_AND_ANALYSE\n'
    'EXECUTION008_GEMINI_503_FALSE_BLOCK=REMOVED\n'
    'FACTCHECK008_USER_TOKEN_UI=ABSENT\n'
    'FACTCHECK008_AUTH=APP_PRIVATE_IF_PRESENT_ELSE_SERVER_SIDE_POLICY\n'
    'APPLICATION_ID_STABLE_FROM_006_007=true\n'
    'DEVICE_PASS=NOT_YET_ACQUIRED\n'
)

main = (root / "app/src/main/java/nexus/android/c002/MainActivity.kt").read_text()
for token in [
    'EXECUTION_MAIN_FRAME_HTTP_NON_TERMINAL',
    'EXECUTION_MAIN_FRAME_WEB_ERROR_NON_TERMINAL',
    'resetExecutionAttempt("PROVIDER_SWITCH:$provider")',
    'resetExecutionAttempt("ANALYSE_NEW_ATTEMPT")',
    'TRY_SERVER_SIDE_AUTH_NO_USER_PROMPT',
    'if (token.isNotBlank()) payload.put("token", token)',
]:
    assert token in main, token
assert 'block("EXECUTION_MAIN_FRAME_HTTP_' not in main
assert 'block("EXECUTION_MAIN_FRAME_WEB_ERROR_' not in main
assert 'Fact Check · autorisation interne indisponible' not in main
