from pathlib import Path
import re, subprocess, sys
repo=Path(sys.argv[1]).resolve(); root=Path(sys.argv[2]).resolve()
subprocess.run(['python3',str(repo/'providerresume021'/'derive.py'),str(repo),str(root)],check=True)

# 022 keeps the SAME Android applicationId and SAME WebView profile as 021 so
# provider auth/session and run metadata survive an update. Only version/label change.
p=root/'app/build.gradle.kts'; g=p.read_text()
g=g.replace('versionCode = 22','versionCode = 23')
g,n=re.subn(r'versionName\s*=\s*"0\.0\.22-c002-provider-run-resume021"','versionName = "0.0.23-c002-provider-run-resume-diagnostic022"',g,count=1); assert n==1
assert 'applicationId = "nexus.android.c002.providerrunresume021"' in g
p.write_text(g)

p=root/'app/src/main/AndroidManifest.xml'; m=p.read_text()
assert m.count('android:label="NEXUS C002 PROVIDER RUN RESUME 021"')==1
m=m.replace('android:label="NEXUS C002 PROVIDER RUN RESUME 021"','android:label="NEXUS C002 RUN RESUME DIAGNOSTIC 022"')
p.write_text(m)

main=root/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=main.read_text()

# Replace the generic BLOCK terminal handling so resume-eligible provider failures
# are exposed as an explicit RECOVERABLE window, not as a misleading final BLOCKED.
old='''    private fun block(code: String) {\n        disposeAuthPopup()\n        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")\n        if (::runLatch.isInitialized && runLatchArmed) {\n            if (isResumeEligibleBlock(code) && resumeAttempt < MAX_RESUME_ATTEMPTS) markRunRecoverable(code) else closeRunLatch(RUN_STATE_TERMINAL_BLOCKED)\n        }\n        proofStopped = true\n        currentHeadline = "BLOCKED — $code"\n        currentBody = null\n        if (::status.isInitialized) renderStatus()\n    }\n'''
new='''    private fun block(code: String) {\n        disposeAuthPopup()\n        val recoverable = ::runLatch.isInitialized && runLatchArmed && isResumeEligibleBlock(code) && resumeAttempt < MAX_RESUME_ATTEMPTS\n        if (recoverable) {\n            markRunRecoverable(code)\n            proofStopped = true\n            currentHeadline = "RECOVERABLE — CLOSE AND REOPEN NEXUS NOW"\n            currentBody = "Same provider run is preserved for observer-only resume. No new prompt/send will be allowed. code=$code"\n            if (::status.isInitialized) recordDiagnostic("RUN_RECOVERABLE_WINDOW", if (::webView.isInitialized) webView.url else null, "code=$code;resume_attempt=$resumeAttempt;ttl_ms=$RUN_LATCH_TTL_MS")\n            if (::status.isInitialized) renderStatus()\n            return\n        }\n        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")\n        if (::runLatch.isInitialized && runLatchArmed) closeRunLatch(RUN_STATE_TERMINAL_BLOCKED)\n        proofStopped = true\n        currentHeadline = "BLOCKED — $code"\n        currentBody = null\n        if (::status.isInitialized) renderStatus()\n    }\n'''
assert s.count(old)==1, '021 block anchor'; s=s.replace(old,new)

# Make resume phases visually unambiguous for DEVICE evidence.
s=s.replace('currentHeadline = "RUN RESUME PENDING — same provider run will be observed, not resubmitted"','currentHeadline = "RUN RESUME PENDING 022 — SAME RUN / NO RESUBMIT"')
s=s.replace('currentHeadline = "RUN RESUME — observing existing Claude conversation"','currentHeadline = "RUN RESUME 022 — OBSERVER ONLY / SAME CLAUDE CONVERSATION"')
s=s.replace('recordDiagnostic("RESUME_JOB", origin, "bridge_run_id=$BRIDGE_RUN_ID;resume_attempt=$resumeAttempt;resubmit=false")','recordDiagnostic("RESUME_JOB_022", origin, "bridge_run_id=$BRIDGE_RUN_ID;resume_attempt=$resumeAttempt;resubmit=false;prompt_injection=false;send_click=false")')
main.write_text(s)
