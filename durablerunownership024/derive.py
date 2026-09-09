from pathlib import Path
import re, subprocess, sys
repo=Path(sys.argv[1]).resolve(); root=Path(sys.argv[2]).resolve()
subprocess.run(['python3',str(repo/'runresumeevidence023'/'derive.py'),str(repo),str(root)],check=True)

def one(s,a,b,label):
    assert s.count(a)==1,label
    return s.replace(a,b,1)

p=root/'app/build.gradle.kts'; g=p.read_text()
g=one(g,'applicationId = "nexus.android.c002.runresumeevidence023"','applicationId = "nexus.android.c002.durablerunownership024"','app id')
g=one(g,'versionCode = 24','versionCode = 25','version code')
g,n=re.subn(r'versionName\s*=\s*"0\.0\.24-c002-run-resume-evidence023"','versionName = "0.0.25-c002-durable-run-ownership024"',g,count=1); assert n==1
p.write_text(g)
p=root/'app/src/main/AndroidManifest.xml'; m=p.read_text(); p.write_text(one(m,'NEXUS C002 RUN RESUME EVIDENCE 023','NEXUS C002 DURABLE RUN OWNERSHIP 024','label'))
p=root/'app/src/main/res/layout/activity_main.xml'; x=p.read_text(); x=one(x,'android:maxLines="5"','android:maxLines="7"','panel lines'); x=one(x,'EVIDENCE 023 — MODE=INITIALIZING','EVIDENCE 024 — BOOT=INITIALIZING','panel text'); p.write_text(x)

p=root/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=p.read_text()
s=one(s,'    private var resumeAttempt = 0\n','    private var resumeAttempt = 0\n    private var bootDecision = BOOT_DECISION_INITIALIZING\n','boot field')
start=s.index('        runLatch = getSharedPreferences(RUN_LATCH_PREFS, MODE_PRIVATE)')
end=s.index('\n        renderRunEvidence()\n',start)+len('\n        renderRunEvidence()\n')
boot='''        runLatch = getSharedPreferences(RUN_LATCH_PREFS, MODE_PRIVATE)
        val bootNow = System.currentTimeMillis()
        val priorState = if (runLatch.contains(RUN_LATCH_STATE_KEY)) runLatch.getString(RUN_LATCH_STATE_KEY, RUN_STATE_IDLE) ?: RUN_STATE_IDLE else RUN_STATE_NONE
        val priorStartedAt = runLatch.getLong(RUN_LATCH_STARTED_AT_KEY, 0L)
        val priorLastSeenAt = runLatch.getLong(RUN_LATCH_LAST_SEEN_AT_KEY, priorStartedAt)
        val priorAge = if (priorLastSeenAt > 0L) bootNow - priorLastSeenAt else -1L
        val persistedRunId = runLatch.getString(RUN_LATCH_BRIDGE_RUN_ID_KEY, null)
        val persistedJobId = runLatch.getString(RUN_LATCH_JOB_ID_KEY, null)
        val persistedProvider = runLatch.getString(RUN_LATCH_PROVIDER_KEY, null)
        val persistedFingerprint = runLatch.getString(RUN_LATCH_FINGERPRINT_KEY, null)
        val persistedPhase = runLatch.getString(RUN_LATCH_PHASE_KEY, null)
        val persistedResumeCount = runLatch.getInt(RUN_LATCH_RESUME_COUNT_KEY, 0)
        val resumable = priorState == RUN_STATE_IN_FLIGHT || priorState == RUN_STATE_RECOVERABLE
        val metadataMatches = persistedRunId == BRIDGE_RUN_ID && persistedJobId == JOB_ID && persistedProvider == "ANTHROPIC" && !persistedFingerprint.isNullOrBlank()
        val withinTtl = priorAge in 0..RUN_LATCH_TTL_MS
        bootDecision = when {
            resumable && withinTtl && metadataMatches && persistedResumeCount < MAX_RESUME_ATTEMPTS -> BOOT_DECISION_RESUME
            resumable && !metadataMatches -> BOOT_DECISION_BLOCK_METADATA
            resumable && !withinTtl -> BOOT_DECISION_BLOCK_STALE
            resumable && persistedResumeCount >= MAX_RESUME_ATTEMPTS -> BOOT_DECISION_BLOCK_ATTEMPTS
            priorState == RUN_STATE_NONE || priorState == RUN_STATE_IDLE || priorState == RUN_STATE_TERMINAL_PASS || priorState == RUN_STATE_TERMINAL_BLOCKED -> BOOT_DECISION_FRESH
            else -> BOOT_DECISION_BLOCK_UNKNOWN
        }
        if (!runLatch.edit()
                .putString(RUN_BOOT_DECISION_KEY, bootDecision)
                .putString(RUN_BOOT_PRIOR_STATE_KEY, priorState)
                .putLong(RUN_BOOT_PRIOR_AGE_MS_KEY, priorAge)
                .putString(RUN_BOOT_PRIOR_RUN_ID_KEY, persistedRunId ?: "NONE")
                .putString(RUN_BOOT_PRIOR_PHASE_KEY, persistedPhase ?: "NONE")
                .putString(RUN_BOOT_PRIOR_PROVIDER_KEY, persistedProvider ?: "NONE")
                .putLong(RUN_BOOT_AT_MS_KEY, bootNow).commit()) {
            proofStopped = true; bootDecision = BOOT_DECISION_BLOCK_COMMIT
            currentHeadline = "BLOCKED — ANDROID_RUN_BOOT_SNAPSHOT_COMMIT_FAILED"
            currentBody = "No provider execution is allowed because durable boot ownership could not be recorded."
            renderRunEvidence(); renderStatus(); return
        }
        when (bootDecision) {
            BOOT_DECISION_RESUME -> {
                resumeAttempt = persistedResumeCount; resumePending = true; runLatchArmed = true
                if (!runLatch.edit().putString(RUN_EVIDENCE_MODE_KEY,"RESUME_PENDING").putString(RUN_EVIDENCE_SAME_RUN_KEY,"YES").putString(RUN_EVIDENCE_RESUBMIT_KEY,"FALSE").commit()) {
                    proofStopped=true; currentHeadline="BLOCKED — ANDROID_RUN_RESUME_EVIDENCE_COMMIT_FAILED"; currentBody=null; renderRunEvidence(); renderStatus(); return
                }
                currentHeadline="RUN RESUME PENDING 024 — DURABLE OWNER FOUND / NO RESUBMIT"
                currentBody="prior_state=$priorState;prior_age_ms=$priorAge;resume_attempt=$resumeAttempt"
            }
            BOOT_DECISION_FRESH -> {
                if (!runLatch.edit().putString(RUN_LATCH_STATE_KEY,RUN_STATE_IDLE).remove(RUN_LATCH_STARTED_AT_KEY).remove(RUN_LATCH_LAST_SEEN_AT_KEY)
                        .putString(RUN_EVIDENCE_MODE_KEY,"FRESH_PENDING").putString(RUN_EVIDENCE_SAME_RUN_KEY,"N/A").putString(RUN_EVIDENCE_RESUBMIT_KEY,"N/A")
                        .putInt(RUN_EVIDENCE_EXECUTE_COUNT_KEY,0).putInt(RUN_EVIDENCE_RESUME_COUNT_KEY,0).putInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY,0).putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY,0).commit()) {
                    proofStopped=true; currentHeadline="BLOCKED — ANDROID_RUN_FRESH_INIT_COMMIT_FAILED"; currentBody=null; renderRunEvidence(); renderStatus(); return
                }
            }
            else -> {
                proofStopped=true; currentHeadline="BLOCKED — ANDROID_RUN_BOOT_DECISION_${sanitizeCode(bootDecision)}"
                currentBody="prior_state=$priorState;prior_age_ms=$priorAge;prior_phase=${persistedPhase ?: "NONE"}. No fresh execution is permitted."
                renderRunEvidence(); renderStatus(); return
            }
        }
        renderRunEvidence()
'''
s=s[:start]+boot+s[end:]
old='''        currentHeadline = if (resumePending) "DESCRIBE PASS — stable Claude auth — resuming same provider run" else "DESCRIBE PASS — stable Claude auth — execution proof starting"
        currentBody = null
        renderStatus()
        if (resumePending) resumeExecutionProof(origin) else startExecutionProof(origin)
'''
new='''        currentHeadline = when (bootDecision) {
            BOOT_DECISION_RESUME -> "DESCRIBE PASS — durable owner verified — resuming same provider run"
            BOOT_DECISION_FRESH -> "DESCRIBE PASS — fresh boot decision established — execution proof starting"
            else -> "DESCRIBE PASS — boot decision invalid"
        }
        currentBody = null
        renderStatus()
        when (bootDecision) {
            BOOT_DECISION_RESUME -> resumeExecutionProof(origin)
            BOOT_DECISION_FRESH -> startExecutionProof(origin)
            else -> block("ANDROID_BOOT_DECISION_NOT_ESTABLISHED")
        }
'''
s=one(s,old,new,'describe gate')
old='''        runLatch.edit()
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
'''
new='''        val resumeStateCommitted = runLatch.edit()
            .putString(RUN_LATCH_STATE_KEY, RUN_STATE_IN_FLIGHT)
            .putLong(RUN_LATCH_LAST_SEEN_AT_KEY, System.currentTimeMillis())
            .putInt(RUN_LATCH_RESUME_COUNT_KEY, resumeAttempt)
            .putString(RUN_LATCH_PHASE_KEY, "RESUME_DISPATCH")
            .putString(RUN_EVIDENCE_MODE_KEY, "RESUME")
            .putString(RUN_EVIDENCE_SAME_RUN_KEY, "YES")
            .putString(RUN_EVIDENCE_RESUBMIT_KEY, "FALSE")
            .putInt(RUN_EVIDENCE_RESUME_COUNT_KEY, resumeDispatchCount).commit()
        if (!resumeStateCommitted) { block("ANDROID_RUN_STATE_COMMIT_FAILED_RESUME_DISPATCH"); return }
        resumePending = false; executionStarted = true
'''
s=one(s,old,new,'resume commit')
s=one(s,'recordDiagnostic("RESUME_JOB_023"','recordDiagnostic("RESUME_JOB_024"','resume event')
s=one(s,'RUN RESUME 023 — OBSERVER ONLY / SAME CLAUDE CONVERSATION','RUN RESUME 024 — OBSERVER ONLY / DURABLE SAME RUN','resume headline')
old='''        executionStarted = true
        armRunLatch(job)
        recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;external_research=false;run_latch=IN_FLIGHT")
'''
new='''        if (!armRunLatch(job)) {
            proofStopped = true
            currentHeadline = "BLOCKED — ANDROID_RUN_STATE_COMMIT_FAILED_EXECUTE_DISPATCH"
            currentBody = "EXECUTE_JOB was not posted because durable ownership could not be committed."
            renderStatus(); return
        }
        executionStarted = true
        recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;external_research=false;run_latch=IN_FLIGHT;durable_commit=true")
'''
s=one(s,old,new,'execute commit gate')
s=one(s,'    private fun armRunLatch(job: ExecutionJob) {\n        runLatchArmed = true\n        val now = System.currentTimeMillis()\n        runLatch.edit()\n','    private fun armRunLatch(job: ExecutionJob): Boolean {\n        val now = System.currentTimeMillis()\n        val committed = runLatch.edit()\n','arm return')
s=one(s,'            .putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, 0)\n            .apply()\n        renderRunEvidence()\n    }\n','            .putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, 0)\n            .commit()\n        runLatchArmed = committed\n        renderRunEvidence()\n        return committed\n    }\n','arm commit')
s=one(s,'    private fun markRunRecoverable(code: String) {\n        if (!::runLatch.isInitialized || !runLatchArmed) return\n        runLatch.edit().putString(RUN_LATCH_STATE_KEY, RUN_STATE_RECOVERABLE).putLong(RUN_LATCH_LAST_SEEN_AT_KEY, System.currentTimeMillis()).putString(RUN_LATCH_PHASE_KEY, "RECOVERABLE:" + sanitizeCode(code)).apply()\n    }\n','    private fun markRunRecoverable(code: String): Boolean {\n        if (!::runLatch.isInitialized || !runLatchArmed) return false\n        return runLatch.edit().putString(RUN_LATCH_STATE_KEY,RUN_STATE_RECOVERABLE).putLong(RUN_LATCH_LAST_SEEN_AT_KEY,System.currentTimeMillis()).putString(RUN_LATCH_PHASE_KEY,"RECOVERABLE:" + sanitizeCode(code)).commit()\n    }\n','recoverable commit')
s=one(s,'        runLatchArmed = false\n        runLatch.edit()\n            .putString(RUN_LATCH_STATE_KEY, state)\n            .remove(RUN_LATCH_STARTED_AT_KEY)\n            .apply()\n','        val committed = runLatch.edit()\n            .putString(RUN_LATCH_STATE_KEY, state)\n            .remove(RUN_LATCH_STARTED_AT_KEY)\n            .commit()\n        if (committed) runLatchArmed = false\n','close commit')
s=one(s,'runLatch.edit().putInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 1).apply()','runLatch.edit().putInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY, 1).commit()','prompt counter commit')
s=one(s,'runLatch.edit().putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, next).apply()','runLatch.edit().putInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY, next).commit()','send counter commit')
rs=s.index('    private fun renderRunEvidence() {'); re_=s.index('\n    private fun renderStatus() {',rs)
renderer='''    private fun renderRunEvidence() {
        if (!::runEvidence.isInitialized || !::runLatch.isInitialized) return
        val mode=runLatch.getString(RUN_EVIDENCE_MODE_KEY,"INITIALIZING") ?: "INITIALIZING"
        val sameRun=runLatch.getString(RUN_EVIDENCE_SAME_RUN_KEY,"N/A") ?: "N/A"
        val resubmit=runLatch.getString(RUN_EVIDENCE_RESUBMIT_KEY,"N/A") ?: "N/A"
        val phase=runLatch.getString(RUN_LATCH_PHASE_KEY,"NONE") ?: "NONE"
        val provider=runLatch.getString(RUN_LATCH_PROVIDER_KEY,"ANTHROPIC") ?: "ANTHROPIC"
        val persistedRun=runLatch.getString(RUN_LATCH_BRIDGE_RUN_ID_KEY,BRIDGE_RUN_ID) ?: BRIDGE_RUN_ID
        val priorRun=runLatch.getString(RUN_BOOT_PRIOR_RUN_ID_KEY,"NONE") ?: "NONE"
        fun shortRun(v:String)=if(v.length<=16)v else v.take(8)+"…"+v.takeLast(6)
        runEvidence.text=buildString {
            append("EVIDENCE 024 | BOOT=").append(runLatch.getString(RUN_BOOT_DECISION_KEY,bootDecision) ?: bootDecision)
                .append(" | PRIOR_STATE=").append(runLatch.getString(RUN_BOOT_PRIOR_STATE_KEY,"NONE") ?: "NONE")
                .append(" | PRIOR_AGE=").append(runLatch.getLong(RUN_BOOT_PRIOR_AGE_MS_KEY,-1L))
            append("\nMODE=").append(mode).append(" | SAME_RUN=").append(sameRun).append(" | RESUBMIT=").append(resubmit)
            append("\nRUN=").append(shortRun(persistedRun)).append(" | PRIOR_RUN=").append(shortRun(priorRun)).append(" | PROVIDER=").append(provider)
            append("\nPRIOR_PHASE=").append((runLatch.getString(RUN_BOOT_PRIOR_PHASE_KEY,"NONE") ?: "NONE").take(48))
            append("\nPHASE=").append(phase.take(48))
            append("\nEXECUTE_JOB=").append(runLatch.getInt(RUN_EVIDENCE_EXECUTE_COUNT_KEY,0)).append(" | RESUME_JOB=").append(runLatch.getInt(RUN_EVIDENCE_RESUME_COUNT_KEY,0))
            append("\nPROMPT_INJECTION=").append(runLatch.getInt(RUN_EVIDENCE_PROMPT_INJECTION_COUNT_KEY,0)).append(" | SEND_CLICK=").append(runLatch.getInt(RUN_EVIDENCE_SEND_CLICK_COUNT_KEY,0))
        }
    }
'''
s=s[:rs]+renderer+s[re_:]
s=one(s,'        if (recoverable) {\n            markRunRecoverable(code)\n            proofStopped = true\n','        if (recoverable) {\n            if (!markRunRecoverable(code)) { proofStopped=true; currentHeadline="BLOCKED — ANDROID_RUN_STATE_COMMIT_FAILED_RECOVERABLE"; currentBody="RECOVERABLE was not advertised because durable ownership could not be committed."; if (::status.isInitialized) renderStatus(); return }\n            proofStopped = true\n','recoverable gate')
s=one(s,'const val RUN_LATCH_PREFS = "nexus_v005_provider_run_resume_021"','const val RUN_LATCH_PREFS = "nexus_v005_durable_run_ownership_024"','prefs')
anchor='        const val RUN_EVIDENCE_SEND_CLICK_COUNT_KEY = "evidence_send_click_count"\n'
keys=anchor+'''        const val RUN_BOOT_DECISION_KEY = "boot_decision"
        const val RUN_BOOT_PRIOR_STATE_KEY = "boot_prior_state"
        const val RUN_BOOT_PRIOR_AGE_MS_KEY = "boot_prior_age_ms"
        const val RUN_BOOT_PRIOR_RUN_ID_KEY = "boot_prior_run_id"
        const val RUN_BOOT_PRIOR_PHASE_KEY = "boot_prior_phase"
        const val RUN_BOOT_PRIOR_PROVIDER_KEY = "boot_prior_provider"
        const val RUN_BOOT_AT_MS_KEY = "boot_at_ms"
        const val RUN_STATE_NONE = "NONE"
        const val BOOT_DECISION_INITIALIZING = "INITIALIZING"
        const val BOOT_DECISION_RESUME = "RESUME"
        const val BOOT_DECISION_FRESH = "FRESH"
        const val BOOT_DECISION_BLOCK_METADATA = "BLOCK_METADATA_MISMATCH"
        const val BOOT_DECISION_BLOCK_STALE = "BLOCK_STALE_OWNER"
        const val BOOT_DECISION_BLOCK_ATTEMPTS = "BLOCK_RESUME_ATTEMPTS"
        const val BOOT_DECISION_BLOCK_UNKNOWN = "BLOCK_UNKNOWN_STATE"
        const val BOOT_DECISION_BLOCK_COMMIT = "BLOCK_BOOT_COMMIT"
'''
s=one(s,anchor,keys,'boot keys')
p.write_text(s)
