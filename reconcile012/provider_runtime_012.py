from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Build strictly on provider runtime 010, which fixed the JS syntax/BRIDGE_READY regression.
exec((repo / "reconcile010" / "provider_runtime_010.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile010" / "provider_runtime_010.py"),
    "sys": sys,
})

main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main_path.read_text()

# GOLDEN-FIRST — ChatGPT Android GP-V005-CHATGPT-ANDROID-UIRETRY1:
# M-024 conversion accidentally placed research_policy on expected_result_pack.audit
# (first research_policy_contract occurrence) instead of on the provider envelope.
# Restore the actual envelope field so the validated provider adapter can execute.
envelope_old = '''            .put("question", job.question)
            .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")
            .put("canonical_rights", "NONE")
'''
envelope_new = '''            .put("question", job.question)
            .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")
            .put("research_policy", job.researchPolicy.name)
            .put("canonical_rights", "NONE")
'''
assert s.count(envelope_old) == 1, "provider envelope M024 anchor missing/ambiguous"
s = s.replace(envelope_old, envelope_new, 1)

# Preserve the historical Android Result Pack audit invariant used by the Golden
# ChatGPT/Gemini paths and by validateResultPack: external_research=false for this
# FORBIDDEN replay. Keep the M024 policy metadata as additional provenance.
audit_old = '''            .put("audit", JSONObject()
                .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")
                .put("research_policy", job.researchPolicy.name)
                .put("canonical_write", false)
'''
audit_new = '''            .put("audit", JSONObject()
                .put("external_research", false)
                .put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")
                .put("research_policy", job.researchPolicy.name)
                .put("canonical_write", false)
'''
assert s.count(audit_old) == 1, "expected result audit anchor missing/ambiguous"
s = s.replace(audit_old, audit_new, 1)
main_path.write_text(s)

# GOLDEN-FIRST — Gemini Android GP-V004-GEMINI-ANDROID-001:
# Runtime 010 inherited a later diagnostic rule that classified a visible composer
# without a visible Google account control as GUEST_READY. The certified V004
# DEVICE path instead treats a visible composer with no visible login action as
# authenticated. Restore exactly that certified decision rule while preserving
# Runtime 010 bridge readiness and M024 policy transport.
gemini_path = root / "app/src/main/assets/nexus/gemini_provider_c002.js"
g = gemini_path.read_text()
auth_old = '''    if(composer && profiles.length>0){
      state='AUTHENTICATED';
      reason='VISIBLE_GEMINI_COMPOSER_AND_GOOGLE_ACCOUNT_CONTROL';
      lastStableAuthState='AUTHENTICATED';
    }else if(composer){
      state='GUEST_READY';
      reason=negatives.length?'VISIBLE_GEMINI_COMPOSER_WITH_LOGIN_ACTION':'VISIBLE_GEMINI_COMPOSER_WITHOUT_ACCOUNT_CONTROL';
      lastStableAuthState='GUEST_READY';
    }else if(!composer && negatives.length>0){
      state='UNAUTHENTICATED';
      reason='VISIBLE_LOGIN_ACTION_AND_NO_GEMINI_COMPOSER';
      lastStableAuthState='UNAUTHENTICATED';
    }else if(lastStableAuthState){
'''
auth_new = '''    if(composer && negatives.length===0){
      state='AUTHENTICATED';
      reason=profiles.length?'VISIBLE_GEMINI_COMPOSER_AND_GOOGLE_ACCOUNT_CONTROL':'VISIBLE_GEMINI_COMPOSER_AND_NO_LOGIN_ACTION';
      lastStableAuthState='AUTHENTICATED';
    }else if(!composer && negatives.length>0){
      state='UNAUTHENTICATED';
      reason='VISIBLE_LOGIN_ACTION_AND_NO_GEMINI_COMPOSER';
      lastStableAuthState='UNAUTHENTICATED';
    }else if(lastStableAuthState){
'''
assert g.count(auth_old) == 1, "Gemini diagnostic auth rule anchor missing/ambiguous"
g = g.replace(auth_old, auth_new, 1)
gemini_path.write_text(g)

# Candidate identity.
gradle = root / "app/build.gradle.kts"
x = gradle.read_text()
assert "versionCode = 64" in x
assert 'versionName = "0.0.64-v007-m024-u013-provider-runtime010"' in x
x = x.replace("versionCode = 64", "versionCode = 65", 1)
x = x.replace(
    'versionName = "0.0.64-v007-m024-u013-provider-runtime010"',
    'versionName = "0.0.65-v007-m024-u013-provider-runtime012-golden-replay"',
    1
)
gradle.write_text(x)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME012_METHOD=GOLDEN_FIRST\n"
    "PROVIDER_RUNTIME012_CHATGPT_GOLDEN=GP-V005-CHATGPT-ANDROID-UIRETRY1\n"
    "PROVIDER_RUNTIME012_CHATGPT_FIX=M024_RESEARCH_POLICY_ON_PROVIDER_ENVELOPE\n"
    "PROVIDER_RUNTIME012_RESULT_AUDIT=EXTERNAL_RESEARCH_FALSE_PRESERVED_FOR_FORBIDDEN_REPLAY\n"
    "PROVIDER_RUNTIME012_GEMINI_GOLDEN=GP-V004-GEMINI-ANDROID-001\n"
    "PROVIDER_RUNTIME012_GEMINI_AUTH=COMPOSER_AND_NO_LOGIN_ACTION_IS_AUTHENTICATED\n"
    "PROVIDER_RUNTIME012_BRIDGE_BASE=RUNTIME010_PRESERVED\n"
    "FACTCHECK012=UNCHANGED_SERVER_AUTH_BLOCKER_O24_UNAUTHORIZED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Static non-regression assertions.
main = main_path.read_text()
gemini = gemini_path.read_text()
assert main.count('.put("research_policy", job.researchPolicy.name)') >= 2
assert '.put("external_research", false)' in main
assert "composer && negatives.length===0" in gemini
assert "VISIBLE_GEMINI_COMPOSER_AND_NO_LOGIN_ACTION" in gemini
assert "state='GUEST_READY'" not in gemini
assert "type:'BRIDGE_READY'" in gemini
