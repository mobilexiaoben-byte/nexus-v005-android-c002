from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
main = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
gradle = root / "app/build.gradle.kts"
lock = root / "RECONCILIATION_LOCK.txt"

text = main.read_text()

# Keep manual provider login/confirmation as the authoritative UX.
# Fix only the stale AUTH REQUIRED state after explicit user confirmation.
old = '''        providerConfirmedByUser = true
        providerSelectionRequested = false
        lastProviderOrigin = expectedOrigin
        webView.visibility = View.GONE
'''
new = '''        providerConfirmedByUser = true
        providerSelectionRequested = false
        lastProviderOrigin = expectedOrigin
        describePassed = true
        lastAuthState = "USER_CONFIRMED"
        currentHeadline = "DESCRIBE PASS — $provider ready (manual confirmation)"
        currentBody = null
        webView.visibility = View.GONE
'''
assert old in text, "manual confirmation anchor missing"
text = text.replace(old, new, 1)

old = '''        productState.text = "$provider · connecté (confirmé par l’utilisateur)"
        recordDiagnostic("PROVIDER_CONFIRMATION", selectedProviderOrigin ?: "", "USER_CONFIRMED_CONNECTED")
    }
'''
new = '''        productState.text = "$provider · connecté (confirmé par l’utilisateur)"
        recordDiagnostic("PROVIDER_CONFIRMATION", selectedProviderOrigin ?: "", "USER_CONFIRMED_CONNECTED;DESCRIBE_OVERRIDE=MANUAL_CONFIRMATION")
        renderStatus()
    }
'''
assert old in text, "manual confirmation completion anchor missing"
text = text.replace(old, new, 1)

# Reset all per-execution state while preserving selected provider/session confirmation.
old = '''    private fun resetExecutionAttempt(reason: String) {
        monitorReset()
        executionStarted = false
        proofStopped = false
        terminalReceived = false
        productRunRequested = false
        currentBody = null
        recordDiagnostic("EXECUTION_STATE_RESET", selectedProviderOrigin ?: "", reason)
    }
'''
new = '''    private fun resetExecutionAttempt(reason: String) {
        monitorReset()
        executionStarted = false
        ackPassed = false
        terminalReceived = false
        proofStopped = false
        proofJob = null
        productRunRequested = false
        currentBody = null
        if (reason.startsWith("PROVIDER_SWITCH:")) {
            describePassed = false
            lastAuthState = null
        }
        recordDiagnostic("EXECUTION_STATE_RESET", selectedProviderOrigin ?: "", reason)
    }
'''
assert old in text, "execution reset anchor missing"
text = text.replace(old, new, 1)

# Every Analyse click gets a new request/job id; the engine duplicate guard remains intact.
old = '''            resetExecutionAttempt("ANALYSE_NEW_ATTEMPT")
            productRunRequested = true
            activeUserQuestion = userQuestion
'''
new = '''            resetExecutionAttempt("ANALYSE_NEW_ATTEMPT")
            activeExecutionId = "U013-ANDROID-" + System.currentTimeMillis() + "-" + java.util.UUID.randomUUID().toString()
            productRunRequested = true
            activeUserQuestion = userQuestion
'''
assert old in text, "analyse click anchor missing"
text = text.replace(old, new, 1)

old = '''    private var lastProviderOrigin: String? = null
    private var activeUserQuestion: String? = null
    private var activeFactCheckJobId: String? = null
'''
new = '''    private var lastProviderOrigin: String? = null
    private var activeUserQuestion: String? = null
    private var activeExecutionId: String = ""
    private var activeFactCheckJobId: String? = null
'''
assert old in text, "active execution state anchor missing"
text = text.replace(old, new, 1)

old = '''        val input = ExecutionInput(
            requestId = JOB_ID,
'''
new = '''        if (activeExecutionId.isBlank()) {
            activeExecutionId = "U013-ANDROID-" + System.currentTimeMillis() + "-" + java.util.UUID.randomUUID().toString()
        }
        val input = ExecutionInput(
            requestId = activeExecutionId,
'''
assert old in text, "ExecutionInput JOB_ID anchor missing"
text = text.replace(old, new, 1)

old = '''        recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;job_type=${jobType.name};research_policy=${job.researchPolicy.name}")
'''
new = '''        recordDiagnostic("EXECUTE_JOB", origin, "job_id=${job.jobId};job_type=${jobType.name};research_policy=${job.researchPolicy.name}")
'''
assert old in text, "EXECUTE_JOB diagnostic anchor missing"
text = text.replace(old, new, 1)

# Keep the historical constant only as a labelled legacy reference, never as an execution id.
old = '        const val JOB_ID = "U013-ANDROID-UX-SHARED-001-JOB-001"\n'
new = '        const val LEGACY_JOB_ID_REFERENCE = "U013-ANDROID-UX-SHARED-001-JOB-001"\n'
assert old in text, "legacy JOB_ID constant anchor missing"
text = text.replace(old, new, 1)

main.write_text(text)

# Candidate identity only; no canonical/release promotion.
g = gradle.read_text()
assert "versionCode = 74" in g
assert 'versionName = "0.0.74-v007-golden-recovery002-device-fixes"' in g
g = g.replace("versionCode = 74", "versionCode = 75", 1)
g = g.replace('versionName = "0.0.74-v007-golden-recovery002-device-fixes"',
              'versionName = "0.0.75-v007-golden-recovery003-auth-exec-fix"', 1)
gradle.write_text(g)

lock.write_text(lock.read_text() +
    "GOLDEN_RECOVERY003_AUTH_MODE=MANUAL_LOGIN_AND_CONFIRMATION_PRESERVED\n"
    "GOLDEN_RECOVERY003_AUTH_FIX=MANUAL_CONFIRMATION_CLEARS_STALE_AUTH_REQUIRED_AND_FREEZES_DESCRIBE_FOR_SELECTED_ORIGIN\n"
    "GOLDEN_RECOVERY003_EXECUTION_ID=UNIQUE_PER_ANALYSE_CLICK\n"
    "GOLDEN_RECOVERY003_DUPLICATE_GUARD=PRESERVED\n"
    "GOLDEN_RECOVERY003_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Scope guards.
out = main.read_text()
assert 'private val manualProviderConfirmationMode = true' in out
assert 'DESCRIBE_OVERRIDE=MANUAL_CONFIRMATION' in out
assert 'currentHeadline = "DESCRIBE PASS — $provider ready (manual confirmation)"' in out
assert 'activeExecutionId = "U013-ANDROID-" + System.currentTimeMillis()' in out
assert 'requestId = activeExecutionId' in out
assert 'const val LEGACY_JOB_ID_REFERENCE' in out
assert 'const val JOB_ID =' not in out
assert 'ackPassed = false' in out
assert 'proofJob = null' in out
