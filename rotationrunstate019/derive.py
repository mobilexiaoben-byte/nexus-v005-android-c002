from pathlib import Path
import subprocess
import sys

repo=Path(sys.argv[1]).resolve()
work=Path(sys.argv[2]).resolve()
subprocess.run(['python3', str(repo/'providercomposersync018'/'derive.py'), str(repo), str(work)], check=True)
root=work

# Identity only: keep provider adapters and bridge behavior from 018 unchanged.
p=root/'app/build.gradle.kts'; g=p.read_text()
for before,after in [
    ('applicationId = "nexus.android.c002.providercomposersync018"','applicationId = "nexus.android.c002.rotationrunstate019"'),
    ('versionCode = 19','versionCode = 20'),
    ('versionName = "0.0.19-c002-provider-composersync018"','versionName = "0.0.20-c002-rotation-runstate019"')
]:
    assert g.count(before)==1, before
    g=g.replace(before,after)
p.write_text(g)

# Rotation must not recreate MainActivity/WebView. Configuration changes are handled in place.
p=root/'app/src/main/AndroidManifest.xml'; m=p.read_text()
old='''        <activity\n            android:name=".MainActivity"\n            android:exported="true">'''
new='''        <activity\n            android:name=".MainActivity"\n            android:exported="true"\n            android:configChanges="orientation|screenSize|screenLayout|smallestScreenSize|keyboardHidden">'''
assert m.count(old)==1, 'activity manifest anchor'
m=m.replace(old,new)
old_label='android:label="NEXUS C002 PROVIDER COMPOSER SYNC 018"'
assert m.count(old_label)==1
m=m.replace(old_label,'android:label="NEXUS C002 ROTATION RUNSTATE SAFE 019"')
p.write_text(m)

main=root/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=main.read_text()

# Imports for configuration handling and a short-lived persistent run latch.
old='''import android.app.Activity\nimport android.net.Uri\n'''
new='''import android.app.Activity\nimport android.content.SharedPreferences\nimport android.content.res.Configuration\nimport android.net.Uri\n'''
assert s.count(old)==1, 'import anchor'
s=s.replace(old,new)

# Build/profile identity. Do not alter the provider proof contract/token in 019.
assert 'nexus_provider_profile_c002_provider_composersync018' in s
s=s.replace('nexus_provider_profile_c002_provider_composersync018','nexus_provider_profile_c002_rotationrunstate019')

field_anchor='''    private var lastAuthState: String? = null\n'''
field_block='''    private var lastAuthState: String? = null\n    private lateinit var runLatch: SharedPreferences\n    private var runLatchArmed = false\n'''
assert s.count(field_anchor)==1, 'field anchor'
s=s.replace(field_anchor,field_block)

# Read the latch after views exist but before any WebView/bridge initialization. If a true Activity
# recreation happens while a run is still recent/in-flight, fail closed instead of silently creating
# a second provider run. Orientation changes do not reach this path because configChanges keeps the
# Activity alive.
click_anchor='''        status.setOnClickListener {\n            diagnosticExpanded = !diagnosticExpanded\n            renderStatus()\n        }\n\n'''
click_new='''        status.setOnClickListener {\n            diagnosticExpanded = !diagnosticExpanded\n            renderStatus()\n        }\n\n        runLatch = getSharedPreferences(RUN_LATCH_PREFS, MODE_PRIVATE)\n        val priorState = runLatch.getString(RUN_LATCH_STATE_KEY, RUN_STATE_IDLE) ?: RUN_STATE_IDLE\n        val priorStartedAt = runLatch.getLong(RUN_LATCH_STARTED_AT_KEY, 0L)\n        val priorAge = System.currentTimeMillis() - priorStartedAt\n        if (priorState == RUN_STATE_IN_FLIGHT && priorAge in 0..RUN_LATCH_TTL_MS) {\n            proofStopped = true\n            currentHeadline = "BLOCKED — ANDROID_INFLIGHT_RUN_RECREATION_DETECTED"\n            currentBody = "A recent provider run is latched in-flight; duplicate auto-start is forbidden. age_ms=$priorAge"\n            runLatch.edit().putString(RUN_LATCH_STATE_KEY, RUN_STATE_RECREATION_BLOCKED).apply()\n            renderStatus()\n            return\n        }\n        runLatch.edit()\n            .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IDLE)\n            .remove(RUN_LATCH_STARTED_AT_KEY)\n            .apply()\n\n'''
assert s.count(click_anchor)==1, 'status click anchor'
s=s.replace(click_anchor,click_new)

# Handle rotation in-place; never reload the provider page and never reset execution flags.
oncreate_end='''        renderStatus()\n        webView.loadUrl("$CHATGPT_ORIGIN/")\n    }\n\n    private fun handleBridgeMessage(origin: String, payload: String) {\n'''
onconfig='''        renderStatus()\n        webView.loadUrl("$CHATGPT_ORIGIN/")\n    }\n\n    override fun onConfigurationChanged(newConfig: Configuration) {\n        super.onConfigurationChanged(newConfig)\n        val orientation = when (newConfig.orientation) {\n            Configuration.ORIENTATION_LANDSCAPE -> "LANDSCAPE"\n            Configuration.ORIENTATION_PORTRAIT -> "PORTRAIT"\n            else -> "UNDEFINED"\n        }\n        recordDiagnostic(\n            "CONFIGURATION_CHANGED",\n            if (::webView.isInitialized) webView.url else null,\n            "orientation=$orientation;execution_in_progress=${executionStarted && !terminalReceived && !proofStopped};webview_preserved=true"\n        )\n    }\n\n    private fun handleBridgeMessage(origin: String, payload: String) {\n'''
assert s.count(oncreate_end)==1, 'onCreate end anchor'
s=s.replace(oncreate_end,onconfig)

# Helper functions centralize run-latch lifecycle. The latch is intentionally short-lived and contains
# no prompt, response, cookies, provider secrets or conversation content.
helper_anchor='''    private fun handleProviderAck(message: JSONObject) {\n'''
helpers='''    private fun armRunLatch() {\n        runLatchArmed = true\n        runLatch.edit()\n            .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IN_FLIGHT)\n            .putLong(RUN_LATCH_STARTED_AT_KEY, System.currentTimeMillis())\n            .apply()\n    }\n\n    private fun closeRunLatch(state: String) {\n        if (!::runLatch.isInitialized) return\n        runLatchArmed = false\n        runLatch.edit()\n            .putString(RUN_LATCH_STATE_KEY, state)\n            .remove(RUN_LATCH_STARTED_AT_KEY)\n            .apply()\n    }\n\n    private fun handleProviderAck(message: JSONObject) {\n'''
assert s.count(helper_anchor)==1, 'ack anchor'
s=s.replace(helper_anchor,helpers)

# Arm before the provider post. Any recreation after this point is not allowed to auto-start another run.
start_anchor='''        executionStarted = true\n        recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;external_research=false")\n'''
start_new='''        executionStarted = true\n        armRunLatch()\n        recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;external_research=false;run_latch=IN_FLIGHT")\n'''
assert s.count(start_anchor)==1, 'execution start anchor'
s=s.replace(start_anchor,start_new)

# Close the latch only after a fully validated terminal receipt.
pass_anchor='''        proofStopped = true\n        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")\n'''
pass_new='''        proofStopped = true\n        closeRunLatch(RUN_STATE_TERMINAL_PASS)\n        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")\n'''
assert s.count(pass_anchor)==1, 'terminal pass anchor'
s=s.replace(pass_anchor,pass_new)

# Any fail-closed terminal also closes the in-flight latch so a later deliberate cold launch can start cleanly.
block_anchor='''    private fun block(code: String) {\n        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")\n        proofStopped = true\n'''
block_new='''    private fun block(code: String) {\n        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")\n        if (::runLatch.isInitialized && runLatchArmed) closeRunLatch(RUN_STATE_TERMINAL_BLOCKED)\n        proofStopped = true\n'''
assert s.count(block_anchor)==1, 'block anchor'
s=s.replace(block_anchor,block_new)

# Constants only; no provider/session content is persisted.
companion_anchor='''    companion object {\n        const val PROFILE_NAME = "nexus_provider_profile_c002_rotationrunstate019"\n'''
companion_new='''    companion object {\n        const val RUN_LATCH_PREFS = "nexus_v005_rotation_runstate_019"\n        const val RUN_LATCH_STATE_KEY = "state"\n        const val RUN_LATCH_STARTED_AT_KEY = "started_at_ms"\n        const val RUN_STATE_IDLE = "IDLE"\n        const val RUN_STATE_IN_FLIGHT = "IN_FLIGHT"\n        const val RUN_STATE_RECREATION_BLOCKED = "RECREATION_BLOCKED"\n        const val RUN_STATE_TERMINAL_PASS = "TERMINAL_PASS"\n        const val RUN_STATE_TERMINAL_BLOCKED = "TERMINAL_BLOCKED"\n        const val RUN_LATCH_TTL_MS = 300_000L\n        const val PROFILE_NAME = "nexus_provider_profile_c002_rotationrunstate019"\n'''
assert s.count(companion_anchor)==1, 'companion anchor'
s=s.replace(companion_anchor,companion_new)

main.write_text(s)
