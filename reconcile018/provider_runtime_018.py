from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Build strictly on Runtime017: M-024 Runtime016 + rotation Runtime014 +
# compact monitor Runtime015 + report panel Runtime017 remain preserved.
exec((repo / "reconcile017" / "provider_runtime_017.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile017" / "provider_runtime_017.py"),
    "sys": sys,
})

main_path = root / "app/src/main/java/nexus/android/c002/MainActivity.kt"
s = main_path.read_text()

# Root cause found by CI inspection:
# handleStatus validated every provider descriptor against CHATGPT_ORIGIN.
# That makes authenticated Gemini/Z.ai fail target validation.
old = '        val gate = RuntimeGate.validateDescriptor(descriptor, CHATGPT_ORIGIN)\n'
new = '''        val expectedProviderOrigin = canonicalOrigin(selectedProviderOrigin ?: origin)
        val gate = RuntimeGate.validateDescriptor(descriptor, expectedProviderOrigin)
'''
assert s.count(old) == 1, "global CHATGPT_ORIGIN descriptor gate anchor missing/ambiguous"
s = s.replace(old, new, 1)

# Provider-neutral status after DESCRIBE PASS.
old = '        currentHeadline = "DESCRIBE PASS — ChatGPT ready"\n'
new = '        currentHeadline = "DESCRIBE PASS — ${selectedProvider ?: "LLM"} ready"\n'
assert s.count(old) == 1, "hardcoded ChatGPT DESCRIBE headline anchor missing"
s = s.replace(old, new, 1)

# Keep visible product state coherent once the selected provider is both
# authenticated and user-confirmed.
anchor = '''        currentBody = null
        renderStatus()
        if (productRunRequested && !activeUserQuestion.isNullOrBlank()) startExecutionProof(origin)
'''
replacement = '''        currentBody = null
        if (providerConfirmedByUser && ::productState.isInitialized) {
            productState.text = "${selectedProvider ?: "LLM"} · connecté · prêt"
        }
        renderStatus()
        if (productRunRequested && !activeUserQuestion.isNullOrBlank()) startExecutionProof(origin)
'''
assert s.count(anchor) == 1, "DESCRIBE PASS render anchor missing"
s = s.replace(anchor, replacement, 1)

# Never label every BLOCKED state as a security challenge. Surface the real
# fail-closed code through the existing user-safe mapper.
old = '''        raw.startsWith("AUTH REQUIRED") -> "Connexion à ChatGPT requise"
'''
new = '''        raw.startsWith("AUTH REQUIRED") -> "Connexion à ${selectedProvider ?: "LLM"} requise"
'''
assert s.count(old) == 1, "AUTH friendly headline anchor missing"
s = s.replace(old, new, 1)

old = '        raw.startsWith("BLOCKED") -> "Exécution bloquée · vérification de sécurité"\n'
new = '''        raw.startsWith("BLOCKED") -> {
            val code = raw.removePrefix("BLOCKED").trim().trimStart('—', '·', ':').trim()
            if (code.isBlank()) "Exécution bloquée"
            else "Exécution bloquée · " + safeMonitorText(code)
        }
'''
assert s.count(old) == 1, "generic security BLOCKED headline anchor missing"
s = s.replace(old, new, 1)

main_path.write_text(s)

gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 70" in g
assert 'versionName = "0.0.70-v007-m024-u013-provider-runtime017-report-panel"' in g
g = g.replace("versionCode = 70", "versionCode = 71", 1)
g = g.replace(
    'versionName = "0.0.70-v007-m024-u013-provider-runtime017-report-panel"',
    'versionName = "0.0.71-v007-m024-u013-provider-runtime018-provider-origin-fix"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME018_BASE=RUNTIME017_REPORT_PANEL\n"
    "PROVIDER_RUNTIME018_ROOT_CAUSE=GLOBAL_DESCRIPTOR_GATE_HARDCODED_CHATGPT_ORIGIN\n"
    "PROVIDER_RUNTIME018_DESCRIPTOR_GATE=SELECTED_PROVIDER_ORIGIN\n"
    "PROVIDER_RUNTIME018_ZAI_FALSE_SECURITY_LABEL=REMOVED_GENERIC_BLOCKED_MAPPING\n"
    "PROVIDER_RUNTIME018_PROVIDER_STATUS=PROVIDER_NEUTRAL_AND_USER_CONFIRMED_READY\n"
    "PROVIDER_RUNTIME018_GEMINI=TARGET_ORIGIN_GATE_CORRECTED\n"
    "M024_RUNTIME016_POLICY_ROUTER=PRESERVED\n"
    "RUNTIME014_ROTATION=PRESERVED\n"
    "RUNTIME015_MONITOR=PRESERVED\n"
    "RUNTIME017_REPORT=PRESERVED\n"
    "V009_ARCH005=FROZEN_UNMODIFIED\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

generated = main_path.read_text()
assert "RuntimeGate.validateDescriptor(descriptor, CHATGPT_ORIGIN)" not in generated
assert "val expectedProviderOrigin = canonicalOrigin(selectedProviderOrigin ?: origin)" in generated
assert "RuntimeGate.validateDescriptor(descriptor, expectedProviderOrigin)" in generated
assert 'DESCRIBE PASS — ${selectedProvider ?: "LLM"} ready' in generated
assert "vérification de sécurité" not in generated
assert 'Connexion à ${selectedProvider ?: "LLM"} requise' in generated
assert "setupExchangeMonitor()" in generated
assert 'text = "Rapport"' in generated

tc = (root / "app/src/main/java/nexus/android/c002/core/TransportContract.kt").read_text()
assert "JobType.OPEN_ANALYSIS -> ResearchPolicy.OPTIONAL" in tc
assert "JobType.CLOSED_AUDIT -> ResearchPolicy.FORBIDDEN" in tc
assert "JobType.POPINT_RESEARCH -> ResearchPolicy.REQUIRED" in tc
