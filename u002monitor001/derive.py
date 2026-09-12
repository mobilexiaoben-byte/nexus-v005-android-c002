from pathlib import Path
import subprocess, sys

repo=Path(sys.argv[1]).resolve()
work=Path(sys.argv[2]).resolve()
subprocess.run(['python3',str(repo/'zaiproof001'/'derive.py'),str(repo),str(work)],check=True)

p=work/'app/build.gradle.kts'; s=p.read_text()
for a,b in [
('applicationId = "nexus.android.c002.zaiexecutionproof001"','applicationId = "nexus.android.c002.u002monitor001"'),
('versionCode = 28','versionCode = 29'),
('versionName = "0.0.28-v005-zai-android-proof001"','versionName = "0.0.29-u002-android-monitor001"')]:
    assert s.count(a)==1,a; s=s.replace(a,b)
p.write_text(s)

p=work/'app/src/main/AndroidManifest.xml'; s=p.read_text()
a='android:label="NEXUS ZAI ANDROID PROOF 001"'; assert s.count(a)==1
p.write_text(s.replace(a,'android:label="NEXUS U002 ANDROID MONITOR TEST"'))

m=work/'app/src/main/java/nexus/android/c002/core/U002Monitor.kt'
m.write_text('''package nexus.android.c002.core\n\nimport android.content.Context\nimport org.json.JSONObject\nimport java.io.File\nimport java.util.UUID\n\nclass U002Monitor(context: Context) {\n    private val file = File(context.filesDir, "u002_monitor_events.jsonl")\n    private val sessionId = UUID.randomUUID().toString()\n    @Synchronized fun record(event: String, fields: Map<String, Any?> = emptyMap()) {\n        runCatching {\n            val out = JSONObject().put("monitor_contract","U002_ANDROID_MONITOR_V1")\n                .put("monitor_build","U002-ANDROID-MONITOR-001")\n                .put("session_id",sessionId).put("event",event)\n                .put("observed_at_ms",System.currentTimeMillis())\n            fields.forEach { (k,v) -> out.put(k,v) }\n            file.appendText(out.toString()+"\\n")\n        }\n    }\n}\n''')

p=work/'app/src/main/java/nexus/android/c002/MainActivity.kt'; s=p.read_text()
a='import nexus.android.c002.core.SelectedProvider\n'; assert s.count(a)==1; s=s.replace(a,a+'import nexus.android.c002.core.U002Monitor\n')
a='    private var lastAuthState: String? = null\n'; assert s.count(a)==1; s=s.replace(a,a+'    private lateinit var u002Monitor: U002Monitor\n')
a='        status = findViewById(R.id.status)\n'; assert s.count(a)==1; s=s.replace(a,a+'        u002Monitor = U002Monitor(this)\n        u002Monitor.record("APP_START", mapOf("platform" to "ANDROID", "transport" to TRANSPORT_ID))\n')
a='''        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")\n        currentHeadline = "EXECUTION PROOF PASS — STOP GATE"\n'''
b='''        recordFinalEvent("TERMINAL_RECEIPT_PASS", "job_id=$JOB_ID;answer=$PROOF_TOKEN")\n        u002Monitor.record("TERMINAL_RECEIPT_PASS", mapOf(\n            "job_id" to job.jobId,\n            "bridge_run_id" to BRIDGE_RUN_ID,\n            "context_pack_id" to job.contextPackId,\n            "frozen_fingerprint" to job.frozenFingerprint,\n            "provider_family" to job.providerFamily,\n            "adapter_id" to job.adapterId,\n            "transport" to TRANSPORT_ID,\n            "canonical_write" to false,\n            "state_mutation_mode" to "NONE",\n            "truth_winner" to "NONE",\n            "status" to "COMPLETED"\n        ))\n        currentHeadline = "EXECUTION PROOF PASS — STOP GATE"\n'''
assert s.count(a)==1; s=s.replace(a,b)
a='''        diagnosticEvents.add(DiagnosticEvent(diagnosticSequence, fingerprint, line))\n        while (diagnosticEvents.size > MAX_DIAGNOSTIC_EVENTS) diagnosticEvents.removeAt(0)\n        renderStatus()\n'''
b='''        diagnosticEvents.add(DiagnosticEvent(diagnosticSequence, fingerprint, line))\n        if (::u002Monitor.isInitialized) u002Monitor.record("TRACE", mapOf("name" to event, "detail" to detailPart))\n        while (diagnosticEvents.size > MAX_DIAGNOSTIC_EVENTS) diagnosticEvents.removeAt(0)\n        renderStatus()\n'''
assert s.count(a)==1; s=s.replace(a,b)
a='''    private fun block(code: String) {\n        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")\n        proofStopped = true\n'''
b='''    private fun block(code: String) {\n        if (!proofStopped && ::status.isInitialized) recordFinalEvent("STOP", "code=$code")\n        if (::u002Monitor.isInitialized) u002Monitor.record("FAIL_CLOSED", mapOf("code" to code, "status" to "FAILED"))\n        proofStopped = true\n'''
assert s.count(a)==1; s=s.replace(a,b)
p.write_text(s)
