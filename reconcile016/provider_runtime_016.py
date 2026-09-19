from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

exec((repo / "reconcile015" / "provider_runtime_015.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile015" / "provider_runtime_015.py"),
    "sys": sys,
})

tc_path = root / "app/src/main/java/nexus/android/c002/core/TransportContract.kt"
main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
test_path = root / "core-tests/TestMain.kt"
assets = root / "app/src/main/assets/nexus"

tc = tc_path.read_text()
old_enum = "enum class ResearchPolicy { FORBIDDEN, ALLOWED, REQUIRED, REQUIRED_IF_STALE }"
new_enum = "enum class ResearchPolicy { FORBIDDEN, OPTIONAL, REQUIRED, REQUIRED_IF_STALE }"
assert old_enum in tc, "Runtime015 ResearchPolicy enum anchor missing"
tc = tc.replace(old_enum, new_enum, 1)

job_router = """
enum class JobType { CLOSED_AUDIT, OPEN_ANALYSIS, FACT_CHECK, POPINT_RESEARCH }

fun resolveResearchPolicy(jobType: JobType): ResearchPolicy = when (jobType) {
    JobType.CLOSED_AUDIT -> ResearchPolicy.FORBIDDEN
    JobType.OPEN_ANALYSIS -> ResearchPolicy.OPTIONAL
    JobType.FACT_CHECK -> ResearchPolicy.REQUIRED
    JobType.POPINT_RESEARCH -> ResearchPolicy.REQUIRED
}

"""
anchor = new_enum + "\n\n"
assert anchor in tc, "policy-router insertion anchor missing"
tc = tc.replace(anchor, anchor + job_router, 1)
tc_path.write_text(tc)

main = main_path.read_text()
old_input = """        val input = ExecutionInput(
            requestId = JOB_ID,
            question = userQuestion,
            handoffText = PROOF_HANDOFF,
            provider = provider,
            model = null,
            researchPolicy = nexus.android.c002.core.ResearchPolicy.FORBIDDEN
        )
"""
new_input = """        val jobType = nexus.android.c002.core.JobType.OPEN_ANALYSIS
        val resolvedResearchPolicy = nexus.android.c002.core.resolveResearchPolicy(jobType)
        val input = ExecutionInput(
            requestId = JOB_ID,
            question = userQuestion,
            handoffText = PROOF_HANDOFF,
            provider = provider,
            model = null,
            researchPolicy = resolvedResearchPolicy
        )
"""
assert main.count(old_input) == 1, "ordinary analysis policy anchor missing/ambiguous"
main = main.replace(old_input, new_input, 1)

audit_policy = '                .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")\n            .put("research_policy", job.researchPolicy.name)'
assert audit_policy in main, "Result Pack policy audit anchor missing"
main = main.replace(
    audit_policy,
    '                .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")\n'
    '                .put("job_type", jobType.name)\n'
    '                .put("research_policy", job.researchPolicy.name)',
    1
)

envelope_policy = '            .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")\n            .put("research_policy", job.researchPolicy.name)'
assert envelope_policy in main, "provider envelope policy anchor missing"
main = main.replace(
    envelope_policy,
    '            .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")\n'
    '            .put("job_type", jobType.name)\n'
    '            .put("research_policy", job.researchPolicy.name)',
    1
)

old_validation = '        if (audit.optBoolean("external_research", true)) return "ANDROID_RESULT_EXTERNAL_RESEARCH_FORBIDDEN"'
new_validation = """        val externalResearchPerformed = audit.optBoolean("external_research", false)
        if (audit.optString("research_policy") != job.researchPolicy.name) return "ANDROID_RESULT_RESEARCH_POLICY_MISMATCH"
        if (job.researchPolicy == nexus.android.c002.core.ResearchPolicy.FORBIDDEN && externalResearchPerformed) return "ANDROID_RESULT_EXTERNAL_RESEARCH_FORBIDDEN"
        if (job.researchPolicy == nexus.android.c002.core.ResearchPolicy.REQUIRED && !externalResearchPerformed) return "ANDROID_RESULT_RESEARCH_REQUIRED_NOT_PERFORMED"
"""
assert main.count(old_validation) == 1, "external-research validation anchor missing/ambiguous"
main = main.replace(old_validation, new_validation, 1)

old_diag = 'recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;external_research=false")'
new_diag = 'recordDiagnostic("EXECUTE_JOB", origin, "job_id=$JOB_ID;job_type=${jobType.name};research_policy=${job.researchPolicy.name}")'
assert old_diag in main, "EXECUTE_JOB diagnostic anchor missing"
main = main.replace(old_diag, new_diag, 1)
main_path.write_text(main)

provider_files = list(assets.glob("*provider*.js"))
assert provider_files, "provider assets missing"
for p in provider_files:
    s = p.read_text()
    if "ALLOWED" in s:
        s = s.replace("ALLOWED", "OPTIONAL")
    s = s.replace(
        "Preserve the expected Result Pack structure and static fields, but replace expected_result_pack.answer with your substantive answer to QUESTION.",
        "Preserve the expected Result Pack structure and static fields, except audit.external_research must truthfully report whether external research was actually used when the resolved policy permits or requires it; replace expected_result_pack.answer with your substantive answer to QUESTION."
    )
    s = s.replace(
        "Preserve expected Result Pack static fields; replace answer with your substantive answer.",
        "Preserve expected Result Pack static fields except audit.external_research, which must truthfully report actual external research use; replace answer with your substantive answer."
    )
    p.write_text(s)

tests = test_path.read_text()
insert_anchor = '    check("T05 policy frozen fingerprint differs", researchJob.frozenFingerprint != job.frozenFingerprint)\n'
assert insert_anchor in tests, "M024 core test anchor missing"
extra = """    check("T05 OPEN_ANALYSIS resolves OPTIONAL", resolveResearchPolicy(JobType.OPEN_ANALYSIS) == ResearchPolicy.OPTIONAL)
    check("T05 CLOSED_AUDIT remains FORBIDDEN", resolveResearchPolicy(JobType.CLOSED_AUDIT) == ResearchPolicy.FORBIDDEN)
    check("T05 POPINT_RESEARCH remains REQUIRED", resolveResearchPolicy(JobType.POPINT_RESEARCH) == ResearchPolicy.REQUIRED)
"""
tests = tests.replace(insert_anchor, insert_anchor + extra, 1)
test_path.write_text(tests)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 68" in g
assert 'versionName = "0.0.68-v007-m024-u013-provider-runtime015-monitor-integrated"' in g
g = g.replace("versionCode = 68", "versionCode = 69", 1)
g = g.replace(
    'versionName = "0.0.68-v007-m024-u013-provider-runtime015-monitor-integrated"',
    'versionName = "0.0.69-v007-m024-u013-provider-runtime016-policy-router-fix"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME016_BASE=RUNTIME015_MONITOR_INTEGRATED\n"
    "M024_ANDROID_JOB_ROUTER=OPEN_ANALYSIS_OPTIONAL,CLOSED_AUDIT_FORBIDDEN,FACT_CHECK_REQUIRED,POPINT_RESEARCH_REQUIRED\n"
    "M024_POLICY_VOCABULARY=FORBIDDEN,OPTIONAL,REQUIRED,REQUIRED_IF_STALE\n"
    "M024_RESULT_AUDIT=POLICY_CORRELATED_AND_EXTERNAL_RESEARCH_ACTUAL\n"
    "M024_REQUIRED_GUARD=RESEARCH_REQUIRED_NOT_PERFORMED_FAIL_EXPLICIT\n"
    "RUNTIME014_ROTATION=PRESERVED\n"
    "RUNTIME015_MONITOR=PRESERVED\n"
    "V009_FROZEN=UNMODIFIED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

tc = tc_path.read_text()
main = main_path.read_text()
assert "ResearchPolicy.ALLOWED" not in tc
assert "ResearchPolicy.OPTIONAL" in tc
assert "JobType.OPEN_ANALYSIS -> ResearchPolicy.OPTIONAL" in tc
assert "JobType.CLOSED_AUDIT -> ResearchPolicy.FORBIDDEN" in tc
assert "researchPolicy = resolvedResearchPolicy" in main
assert '.put("job_type", jobType.name)' in main
assert main.count('.put("research_policy", job.researchPolicy.name)') >= 2
assert "ANDROID_RESULT_RESEARCH_POLICY_MISMATCH" in main
assert "ANDROID_RESULT_RESEARCH_REQUIRED_NOT_PERFORMED" in main
assert "job_type=${jobType.name};research_policy=${job.researchPolicy.name}" in main
assert "monitorOutbound()" in main and "monitorPass()" in main
assert "CONFIGURATION_CHANGED_PRESERVED" in main
for p in provider_files:
    s = p.read_text()
    assert "ALLOWED" not in s, p.name
