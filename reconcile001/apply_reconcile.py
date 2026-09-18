from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()

tc = root / 'app/src/main/java/nexus/android/c002/core/TransportContract.kt'
s = tc.read_text()
if 'enum class ResearchPolicy' not in s:
    s = s.replace(
        'enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI }',
        'enum class SelectedProvider { CHATGPT, CLAUDE, GEMINI }\n\nenum class ResearchPolicy { FORBIDDEN, ALLOWED, REQUIRED, REQUIRED_IF_STALE }'
    )
s = s.replace('    val externalResearch: Boolean = false\n', '    val researchPolicy: ResearchPolicy = ResearchPolicy.FORBIDDEN\n')
s = s.replace(
    '    val handoffText: String,\n    val canonicalWrite:',
    '    val handoffText: String,\n    val researchPolicy: ResearchPolicy,\n    val canonicalWrite:'
)
s = s.replace(
    '        handoffText,\n        canonicalWrite.toString(),',
    '        handoffText,\n        researchPolicy.name,\n        canonicalWrite.toString(),'
)
s = s.replace(
    '    val model: String?,\n    val frozenPackage:',
    '    val model: String?,\n    val researchPolicy: ResearchPolicy,\n    val frozenPackage:'
)
s = s.replace('        require(!input.externalResearch) { "ANDROID_EXTERNAL_RESEARCH_FORBIDDEN" }\n', '')
s = s.replace(
    'val frozen = FrozenPackage(packId, input.question, input.provider, input.model, input.handoffText)',
    'val frozen = FrozenPackage(packId, input.question, input.provider, input.model, input.handoffText, input.researchPolicy)'
)
s = s.replace(
    '            model = input.model,\n            frozenPackage = frozen,',
    '            model = input.model,\n            researchPolicy = input.researchPolicy,\n            frozenPackage = frozen,'
)
for token in ['enum class ResearchPolicy', 'val researchPolicy: ResearchPolicy', 'researchPolicy.name']:
    assert token in s, token
tc.write_text(s)

main = root / 'app/src/main/java/nexus/android/c002/MainActivity.kt'
s = main.read_text()
s = s.replace('.put("external_research", false)', '.put("research_policy_contract", "M024_RESOLVED_POLICY_REQUIRED")')
s = s.replace('externalResearch = false', 'researchPolicy = nexus.android.c002.core.ResearchPolicy.FORBIDDEN')
assert 'M024_RESOLVED_POLICY_REQUIRED' in s
for token in ['FACT CHECK O24', 'productFactCheck', 'nexusMenu', 'Choisir son LLM']:
    assert token in s, token
main.write_text(s)

gradle = root / 'app/build.gradle.kts'
s = gradle.read_text()
s = s.replace('applicationId = "nexus.android.u013.shared009"', 'applicationId = "nexus.android.v007.m024.u013.reconcile001"')
s = s.replace('versionCode = 54', 'versionCode = 55')
s = s.replace(
    'versionName = "0.0.54-u013-android-ux-shared009-o24-dedicated-screen"',
    'versionName = "0.0.55-v007-m024-u013-authfix2-reconcile001"'
)
assert 'nexus.android.v007.m024.u013.reconcile001' in s
assert '0.0.55-v007-m024-u013-authfix2-reconcile001' in s
gradle.write_text(s)

for name in ['chatgpt_provider_c002.js', 'claude_provider_c002.js']:
    p = root / 'app/src/main/assets/nexus' / name
    s = p.read_text()
    old = "if(envelope.external_research!==false) throw new Error('EXTERNAL_RESEARCH_FORBIDDEN');"
    new = "const researchPolicy=String(envelope.research_policy||'');\n      if(!['FORBIDDEN','ALLOWED','REQUIRED','REQUIRED_IF_STALE'].includes(researchPolicy)) throw new Error('EXECUTION_RESEARCH_POLICY_INVALID');"
    if old in s:
        s = s.replace(old, new)
    if "function buildPrompt(envelope){\n    const researchPolicy=" not in s:
        anchor = "  function buildPrompt(envelope){\n    const pack="
        assert anchor in s, f'buildPrompt anchor missing in {name}'
        s = s.replace(
            anchor,
            "  function buildPrompt(envelope){\n    const researchPolicy=String(envelope.research_policy||'');\n    if(!['FORBIDDEN','ALLOWED','REQUIRED','REQUIRED_IF_STALE'].includes(researchPolicy)) throw new Error('EXECUTION_RESEARCH_POLICY_INVALID');\n    const pack="
        )
    policy_marker = "'- Follow the resolved M024 execution policy carried by the envelope.'"
    if policy_marker not in s:
        anchor = "      'FROZEN PACKAGE:',"
        assert anchor in s, f'prompt anchor missing in {name}'
        policy = (
            "      '- Follow the resolved M024 execution policy carried by the envelope.',\n"
            "      (researchPolicy==='FORBIDDEN' ? '- Research policy FORBIDDEN: use only supplied/frozen sources and do not browse.' : researchPolicy==='REQUIRED' ? '- Research policy REQUIRED: perform the external research required by the job and cite/trace sources as required by source_policy.' : researchPolicy==='REQUIRED_IF_STALE' ? '- Research policy REQUIRED_IF_STALE: research externally when freshness or source gaps require it.' : '- Research policy ALLOWED: external research may be used when useful and permitted by source_policy.'),\n"
        )
        s = s.replace(anchor, policy + anchor)
    assert 'EXECUTION_RESEARCH_POLICY_INVALID' in s
    p.write_text(s)

chat = root / 'app/src/main/assets/nexus/chatgpt_provider_c002.js'
chat_s = chat.read_text()
assert 'AUTO_AUTH_MENU_PROBE' in chat_s
assert 'MENU_CLICK_IS_NOT_AUTH_PROOF' in chat_s

test = root / 'core-tests/TestMain.kt'
s = test.read_text()
old = '    check("T05 external research fail closed", runCatching { engine.buildJob(base.copy(requestId="job-er", externalResearch=true)) }.isFailure)'
if old in s:
    new = '\n'.join([
        '    check("T05 closed policy transported", job.researchPolicy == ResearchPolicy.FORBIDDEN && job.frozenPackage.researchPolicy == ResearchPolicy.FORBIDDEN)',
        '    val researchJob = engine.buildJob(base.copy(requestId="job-er", researchPolicy=ResearchPolicy.REQUIRED))',
        '    check("T05 required research policy accepted", researchJob.researchPolicy == ResearchPolicy.REQUIRED && researchJob.frozenPackage.researchPolicy == ResearchPolicy.REQUIRED)',
        '    check("T05 policy frozen fingerprint differs", researchJob.frozenFingerprint != job.frozenFingerprint)',
    ])
    s = s.replace(old, new)
assert 'T05 required research policy accepted' in s
test.write_text(s)

(root / 'RECONCILIATION_LOCK.txt').write_text(
    'CANDIDATE=V007_M024_U013_AUTHFIX2_RECONCILE_001\n'
    'BASELINE_UX=U013_ANDROID_UX_SHARED_009\n'
    'AUTH_RUNTIME=V007_AUTHFIX2_DEVICE_NOMINAL_PASS_LINEAGE\n'
    'EXECUTION_POLICY=M024_RESOLVED_POLICY_REQUIRED\n'
    'FACTCHECK=U013_O24_DEDICATED_SCREEN_PRESERVED\n'
    'MAIN_PRODUCTION_UNCHANGED=true\n'
    'DEVICE_PASS=NOT_YET_ACQUIRED\n'
)
