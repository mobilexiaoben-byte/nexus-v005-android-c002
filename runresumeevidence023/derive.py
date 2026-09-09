from pathlib import Path
import re, subprocess, sys
repo=Path(sys.argv[1]).resolve(); root=Path(sys.argv[2]).resolve()
subprocess.run(['python3',str(repo/'providerresumediag022'/'derive.py'),str(repo),str(root)],check=True)

p=root/'app/build.gradle.kts'; g=p.read_text()
g=g.replace('applicationId = "nexus.android.c002.providerresumediag022"','applicationId = "nexus.android.c002.runresumeevidence023"')
g=g.replace('versionCode = 23','versionCode = 24')
g,n=re.subn(r'versionName\s*=\s*"0\.0\.23-c002-provider-run-resume-diagnostic022"','versionName = "0.0.24-c002-run-resume-evidence023"',g,count=1); assert n==1
p.write_text(g)

p=root/'app/src/main/AndroidManifest.xml'; m=p.read_text()
assert m.count('android:label="NEXUS C002 RUN RESUME DIAGNOSTIC 022"')==1
m=m.replace('android:label="NEXUS C002 RUN RESUME DIAGNOSTIC 022"','android:label="NEXUS C002 RUN RESUME EVIDENCE 023"')
p.write_text(m)

p=root/'app/src/main/res/layout/activity_main.xml'; x=p.read_text()
anchor='''    <WebView
        android:id="@+id/providerWebView"
'''
panel='''    <TextView
        android:id="@+id/runEvidence"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:paddingStart="8dp"
        android:paddingEnd="8dp"
        android:paddingTop="4dp"
        android:paddingBottom="4dp"
        android:maxLines="5"
        android:textSize="11sp"
        android:text="EVIDENCE 023 — MODE=INITIALIZING" />

    <WebView
        android:id="@+id/providerWebView"
'''
assert x.count(anchor)==1
x=x.replace(anchor,panel)
p.write_text(x)

main=root/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=main.read_text()
s=s.replace('''    private lateinit var status: TextView
''','''    private lateinit var status: TextView
    private lateinit var runEvidence: TextView
''',1)
s=s.replace('''        status = findViewById(R.id.status)
        status.setOnClickListener {
''','''        status = findViewById(R.id.status)
        runEvidence = findViewById(R.id.runEvidence)
        status.setOnClickListener {
''',1)
old='''            resumePending = true
            runLatchArmed = true
            currentHeadline = "RUN RESUME PENDING 022 — SAME RUN / NO RESUBMIT"
            currentBody = "state=$priorState;age_ms=$priorAge;resume_attempt=$resumeAttempt"
        } else {
            runLatch.edit().putString(RUN_LATCH_STATE_KEY, RUN_STATE_IDLE).remove(RUN_LATCH_STARTED_AT_KEY).remove(RUN_LATCH_LAST_SEEN_AT_KEY).apply()
        }
'''
new='''            resumePending = true
            runLatchArmed = true
            runLatch.edit()
                .putString(RUN_EVIDENCE_MODE_KEY, "RESUME_PENDING")
                .putString(RUN_EVIDENCE_SAME_RUN_KEY, "YES")
                .putString(RUN_EVIDENCE_RESUBMIT_KEY, "FALSE")
                .apply()
            currentHeadline = "RUN RESUME PENDING 023 — SAME RUN / NO RESUBMIT"
            currentBody = "state=$priorState;age_ms=$priorAge;resume_attempt=$resumeAttempt"
        } else {
            runLatch.edit()
                .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IDLE)
                .remove(RUN_LATCH_STARTED_AT_KEY)
                .remove(RUN_LATCH_LAST_SEEN_AT_KEY)
                .putString(RUN_EVIDENCE_MODE_KEY, "FRESH_PENDING")
                .putString(RUN_EVIDENCE_SAME_RUN_KEY, "N/A")
                .putString(RUN_EVIDENCE_RESUBMIT_KEY, "N/A")
                .putInt(RUN_EVIDENCE_EXECUTE_COUNT_KEY, 0)
                .putInt(RUN_EVIDENCE_RESUME_COUNT_KEY, 0)
                .putInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 0)
                .putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, 0)
                .apply()
        }
        renderRunEvidence()
'''
assert s.count(old)==1; s=s.replace(old,new)
old='''        resumeAttempt += 1
        runLatch.edit().putString(RUN_LATCH_STATE_KEY, RUN_STATE_IN_FLIGHT).putLong(RUN_LATCH_LAST_SEEN_AT_KEY, System.currentTimeMillis()).putInt(RUN_LATCH_RESUME_COUNT_KEY, resumeAttempt).putString(RUN_LATCH_PHASE_KEY, "RESUME_DISPATCH").apply()
        resumePending = false; executionStarted = true
        recordDiagnostic("RESUME_JOB_022", origin, "bridge_run_id=$BRIDGE_RUN_ID;resume_attempt=$resumeAttempt;resubmit=false;prompt_injection=false;send_click=false")
        currentHeadline = "RUN RESUME 022 — OBSERVER ONLY / SAME CLAUDE CONVERSATION"; currentBody = null; renderStatus()
'''
new='''        resumeAttempt += 1
        val resumeDispatchCount = runLatch.getInt(RUN_EVIDENCE_RESUME_COUNT_KEY, 0) + 1
        runLatch.edit()
            .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IN_FLIGHT)
            .putLong(RUN_LATCH_LAST_SEEN_AT_KEY, System.currentTimeMillis())
            .putInt(RUN_LATCH_RESUME_COUNT_KEY, resumeAttempt)
            .putString(RUN_LATCH_PHASE_KEY, "RESUME_DISPATCH")
            .putString(RUN_EVIDENCE_MODE_KEY, "RESUME")
            .putString(RUN_EVIDENCE_SAME_RUN_KEY, "YES")
            .putString(RUN_EVIDENCE_RESUBMIT_KEY, "FALSE")
            .putInt(RUN_EVIDENCE_RESUME_COUNT_KEY, resumeDispatchCount)
            .apply()
        resumePending = false; executionStarted = true
        renderRunEvidence()
        recordDiagnostic("RESUME_JOB_023", origin, "bridge_run_id=$BRIDGE_RUN_ID;resume_attempt=$resumeAttempt;resubmit=false;prompt_injection=false;send_click=false")
        currentHeadline = "RUN RESUME 023 — OBSERVER ONLY / SAME CLAUDE CONVERSATION"; currentBody = null; renderStatus()
'''
assert s.count(old)==1; s=s.replace(old,new)
old='''    private fun armRunLatch(job: ExecutionJob) {
        runLatchArmed = true
        val now = System.currentTimeMillis()
        runLatch.edit()
            .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IN_FLIGHT)
            .putLong(RUN_LATCH_STARTED_AT_KEY, now)
            .putLong(RUN_LATCH_LAST_SEEN_AT_KEY, now)
            .putString(RUN_LATCH_BRIDGE_RUN_ID_KEY, BRIDGE_RUN_ID)
            .putString(RUN_LATCH_JOB_ID_KEY, job.jobId)
            .putString(RUN_LATCH_PROVIDER_KEY, "ANTHROPIC")
            .putString(RUN_LATCH_FINGERPRINT_KEY, job.frozenFingerprint)
            .putString(RUN_LATCH_PHASE_KEY, "EXECUTE_DISPATCH")
            .putInt(RUN_LATCH_RESUME_COUNT_KEY, 0)
            .apply()
    }
'''
new='''    private fun armRunLatch(job: ExecutionJob) {
        runLatchArmed = true
        val now = System.currentTimeMillis()
        runLatch.edit()
            .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IN_FLIGHT)
            .putLong(RUN_LATCH_STARTED_AT_KEY, now)
            .putLong(RUN_LATCH_LAST_SEEN_AT_KEY, now)
            .putString(RUN_LATCH_BRIDGE_RUN_ID_KEY, BRIDGE_RUN_ID)
            .putString(RUN_LATCH_JOB_ID_KEY, job.jobId)
            .putString(RUN_LATCH_PROVIDER_KEY, "ANTHROPIC")
            .putString(RUN_LATCH_FINGERPRINT_KEY, job.frozenFingerprint)
            .putString(RUN_LATCH_PHASE_KEY, "EXECUTE_DISPATCH")
            .putInt(RUN_LATCH_RESUME_COUNT_KEY, 0)
            .putString(RUN_EVIDENCE_MODE_KEY, "FRESH")
            .putString(RUN_EVIDENCE_SAME_RUN_KEY, "N/A")
            .putString(RUN_EVIDENCE_RESUBMIT_KEY, "N/A")
            .putInt(RUN_EVIDENCE_EXECUTE_COUNT_KEY, 1)
            .putInt(RUN_EVIDENCE_RESUME_COUNT_KEY, 0)
            .putInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 0)
            .putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, 0)
            .apply()
        renderRunEvidence()
    }
'''
assert s.count(old)==1; s=s.replace(old,new)
old='''        val jobStatus = message.optString("job_status", "UNKNOWN").take(96)
        markRunProgress(jobStatus)
        recordDiagnostic("PROVIDER_PROGRESS", CLAUDE_ORIGIN, "status=$jobStatus")
'''
new='''        val jobStatus = message.optString("job_status", "UNKNOWN").take(96)
        markRunProgress(jobStatus)
        updateRunEvidenceFromProviderStatus(jobStatus)
        recordDiagnostic("PROVIDER_PROGRESS", CLAUDE_ORIGIN, "status=$jobStatus")
'''
assert s.count(old)==1; s=s.replace(old,new)
anchor='''    private fun renderStatus() {
        status.maxLines = if (diagnosticExpanded) EXPANDED_STATUS_LINES else COMPACT_STATUS_LINES
        status.text = buildString {
            append(currentHeadline)
            val visibleEvents = if (diagnosticExpanded) diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT) else diagnosticEvents.takeLast(1)
            visibleEvents.forEach { event ->
                append("\\n").append(event.line)
                if (event.repeatCount > 1) append(" ×").append(event.repeatCount)
            }
            if (diagnosticExpanded && !currentBody.isNullOrBlank()) append("\\n").append(currentBody)
        }
    }
'''
replacement='''    private fun updateRunEvidenceFromProviderStatus(jobStatus: String) {
        if (!::runLatch.isInitialized) return
        when {
            jobStatus == "CLAUDE_UI_PROMPT_READY" -> {
                if (runLatch.getInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 0) == 0) {
                    runLatch.edit().putInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 1).apply()
                }
            }
            jobStatus == "CLAUDE_UI_PROMPT_CLICK_1" || jobStatus == "CLAUDE_UI_PROMPT_CLICK_2" -> {
                val next = runLatch.getInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, 0) + 1
                runLatch.edit().putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, next).apply()
            }
        }
        renderRunEvidence()
    }

    private fun renderRunEvidence() {
        if (!::runEvidence.isInitialized || !::runLatch.isInitialized) return
        val mode = runLatch.getString(RUN_EVIDENCE_MODE_KEY, "INITIALIZING") ?: "INITIALIZING"
        val sameRun = runLatch.getString(RUN_EVIDENCE_SAME_RUN_KEY, "N/A") ?: "N/A"
        val resubmit = runLatch.getString(RUN_EVIDENCE_RESUBMIT_KEY, "N/A") ?: "N/A"
        val phase = runLatch.getString(RUN_LATCH_PHASE_KEY, "NONE") ?: "NONE"
        val provider = runLatch.getString(RUN_LATCH_PROVIDER_KEY, "ANTHROPIC") ?: "ANTHROPIC"
        val persistedRun = runLatch.getString(RUN_LATCH_BRIDGE_RUN_ID_KEY, BRIDGE_RUN_ID) ?: BRIDGE_RUN_ID
        val runShort = if (persistedRun.length <= 16) persistedRun else persistedRun.take(8) + "…" + persistedRun.takeLast(6)
        runEvidence.text = buildString {
            append("EVIDENCE 023 | MODE=").append(mode)
                .append(" | SAME_RUN=").append(sameRun)
                .append(" | RESUBMIT=").append(resubmit)
            append("\\nRUN=").append(runShort)
                .append(" | PROVIDER=").append(provider)
                .append(" | PHASE=").append(phase.take(48))
            append("\\nEXECUTE_JOB=").append(runLatch.getInt(RUN_EVIDENCE_EXECUTE_COUNT_KEY, 0))
                .append(" | RESUME_JOB=").append(runLatch.getInt(RUN_EVIDENCE_RESUME_COUNT_KEY, 0))
            append("\\nPROMPT_INJECTION=").append(runLatch.getInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 0))
                .append(" | SEND_CLICK=").append(runLatch.getInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, 0))
        }
    }

    private fun renderStatus() {
        status.maxLines = if (diagnosticExpanded) EXPANDED_STATUS_LINES else COMPACT_STATUS_LINES
        status.text = buildString {
            append(currentHeadline)
            val visibleEvents = if (diagnosticExpanded) diagnosticEvents.takeLast(EXPANDED_EVENT_COUNT) else diagnosticEvents.takeLast(1)
            visibleEvents.forEach { event ->
                append("\\n").append(event.line)
                if (event.repeatCount > 1) append(" ×").append(event.repeatCount)
            }
            if (diagnosticExpanded && !currentBody.isNullOrBlank()) append("\\n").append(currentBody)
        }
        renderRunEvidence()
    }
'''
assert s.count(anchor)==1; s=s.replace(anchor,replacement)
anchor='''        const val RUN_LATCH_RESUME_COUNT_KEY = "resume_count"
'''
keys='''        const val RUN_LATCH_RESUME_COUNT_KEY = "resume_count"
        const val RUN_EVIDENCE_MODE_KEY = "evidence_mode"
        const val RUN_EVIDENCE_SAME_RUN_KEY = "evidence_same_run"
        const val RUN_EVIDENCE_RESUBMIT_KEY = "evidence_resubmit"
        const val RUN_EVIDENCE_EXECUTE_COUNT_KEY = "evidence_execute_job_count"
        const val RUN_EVIDENCE_RESUME_COUNT_KEY = "evidence_resume_job_count"
        const val RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY = "evidence_prompt_injection_count"
        const val RUN_EVIDENCE_SEND_CLICK_COUNT_KEY = "evidence_send_click_count"
'''
assert s.count(anchor)==1; s=s.replace(anchor,keys)
main.write_text(s)

provider=root/'app/src/main/assets/nexus/claude_provider_c002.js'; j=provider.read_text()
old='''        send.focus();
        send.click();
        submission=await waitForSubmissionEstablished(bridgeRunId,envelope,turnBaseline,15000);
'''
new='''        send.focus();
        send.click();
        await progress(bridgeRunId,'CLAUDE_UI_PROMPT_CLICK_2');
        submission=await waitForSubmissionEstablished(bridgeRunId,envelope,turnBaseline,15000);
'''
assert j.count(old)==1; j=j.replace(old,new)
provider.write_text(j)
