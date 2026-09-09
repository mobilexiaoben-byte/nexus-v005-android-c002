from pathlib import Path
import subprocess
import sys

repo=Path(sys.argv[1]).resolve()
work=Path(sys.argv[2]).resolve()
subprocess.run(['python3', str(repo/'rotationrunstate019'/'derive.py'), str(repo), str(work)], check=True)
root=work

# 020 changes the Claude submission-proof state machine only. MainActivity, WebView auth/OAuth,
# run-state/rotation handling, ChatGPT, OriginPolicy and NexusWebBridge remain inherited from 019.
p=root/'app/build.gradle.kts'; g=p.read_text()
for before,after in [
    ('applicationId = "nexus.android.c002.rotationrunstate019"','applicationId = "nexus.android.c002.claudesubmissionproof020"'),
    ('versionCode = 20','versionCode = 21'),
    ('versionName = "0.0.20-c002-rotationrunstate019"','versionName = "0.0.21-c002-claude-submission-proof020"')
]:
    assert g.count(before)==1, before
    g=g.replace(before,after)
p.write_text(g)

p=root/'app/src/main/AndroidManifest.xml'; m=p.read_text()
old='android:label="NEXUS C002 ROTATION RUNSTATE SAFE 019"'
assert m.count(old)==1
m=m.replace(old,'android:label="NEXUS C002 CLAUDE SUBMISSION PROOF 020"')
p.write_text(m)

provider=root/'app/src/main/assets/nexus/claude_provider_c002.js'; j=provider.read_text()

old='''  function promptSubmissionSignal(envelope){\n    const composer=findComposer();\n    if(isGenerating()) return 'GENERATION_ACTIVE';\n    if(!composer) return null;\n    const text=composerText(composer).trim();\n    const stillHasPack=text.includes(envelope.context_pack_id);\n    const stillHasTail=text.includes('Generate the completed Result Pack now.');\n    if(!stillHasPack && !stillHasTail && text.length<80) return 'COMPOSER_CLEARED';\n    return null;\n  }\n\n  async function waitForPromptSubmission(envelope,timeout){\n    const deadline=Date.now()+timeout;\n    while(Date.now()<deadline){\n      const signal=promptSubmissionSignal(envelope);\n      if(signal) return signal;\n      await new Promise(r=>setTimeout(r,200));\n    }\n    return null;\n  }\n\n'''
new='''  function composerSubmissionSnapshot(envelope,baseline){\n    const composer=findComposer();\n    const text=composer?composerText(composer).trim():'';\n    const hasPack=!!composer && text.includes(envelope.context_pack_id);\n    const hasTail=!!composer && text.includes('Generate the completed Result Pack now.');\n    const composerCleared=!!composer && !hasPack && !hasTail && text.length<80;\n    const turn=turnGenerationSnapshot(envelope);\n    const userTurn=(turn.po>baseline.po || turn.u>baseline.u);\n    const generation=(turn.g===1 || turn.s>baseline.s || turn.st>baseline.st || turn.a>baseline.a);\n    return {composer_present:!!composer,composer_cleared:composerCleared,has_pack:hasPack,has_tail:hasTail,text_len:text.length,user_turn:userTurn,generation,turn};\n  }\n\n  function compactSubmissionProof(s){\n    return [\n      'S020',\n      'c'+(s.composer_present?1:0),\n      'cc'+(s.composer_cleared?1:0),\n      'hp'+(s.has_pack?1:0),\n      'ht'+(s.has_tail?1:0),\n      'tl'+s.text_len,\n      'u'+(s.user_turn?1:0),\n      'g'+(s.generation?1:0),\n      compactTurnDiag(s.turn)\n    ].join('_');\n  }\n\n  async function waitForSubmissionEstablished(bridgeRunId,envelope,baseline,timeout=12000){\n    const deadline=Date.now()+timeout;\n    let clearedSince=0,last='',lastAt=0,latest=null;\n    while(Date.now()<deadline){\n      latest=composerSubmissionSnapshot(envelope,baseline);\n      if(latest.composer_cleared){\n        if(!clearedSince) clearedSince=Date.now();\n      }else{\n        clearedSince=0;\n      }\n      const stableCleared=clearedSince>0 && Date.now()-clearedSince>=1500;\n      const proof=compactSubmissionProof(latest)+(stableCleared?'_stable1':'_stable0');\n      if(proof!==last || Date.now()-lastAt>=2000){\n        last=proof; lastAt=Date.now();\n        await progress(bridgeRunId,'CLAUDE_SUBMISSION_PROOF__'+proof);\n      }\n      if(stableCleared && (latest.user_turn || latest.generation)){\n        const mode=latest.user_turn&&latest.generation?'USER_TURN_AND_GENERATION':(latest.user_turn?'USER_TURN':'GENERATION');\n        await progress(bridgeRunId,'CLAUDE_SUBMISSION_ESTABLISHED__'+mode+'__'+proof);\n        return {mode,snapshot:latest,proof};\n      }\n      await new Promise(r=>setTimeout(r,250));\n    }\n    const snapshot=latest||composerSubmissionSnapshot(envelope,baseline);\n    return {mode:null,snapshot,proof:compactSubmissionProof(snapshot)};\n  }\n\n'''
assert j.count(old)==1, '018/019 prompt submission heuristic anchor'
j=j.replace(old,new)

old_exec='''      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');\n      send.focus();\n      send.click();\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_CLICK_1');\n      let submission=await waitForPromptSubmission(envelope,4000);\n\n      if(!submission){\n        await progress(bridgeRunId,'CLAUDE_UI_PROMPT_RETRY_1');\n        send=findSendButton();\n        if(!send || !buttonSemanticState(send).ready) throw new Error('CLAUDE_SEND_BUTTON_NOT_READY_ON_RETRY');\n        send.focus();\n        send.click();\n        submission=await waitForPromptSubmission(envelope,6000);\n      }\n\n      if(!submission) throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_CONFIRMED');\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED__'+submission);\n      await waitForTurnAndGeneration(bridgeRunId,envelope,turnBaseline);\n'''
new_exec='''      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_READY');\n      send.focus();\n      send.click();\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_CLICK_1');\n      let submission=await waitForSubmissionEstablished(bridgeRunId,envelope,turnBaseline,6000);\n\n      if(!submission.mode){\n        const snap=submission.snapshot;\n        const retryAllowed=!!snap && snap.has_pack && !snap.user_turn && !snap.generation;\n        if(!retryAllowed){\n          throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_ESTABLISHED_NO_SAFE_RETRY__'+submission.proof);\n        }\n        await progress(bridgeRunId,'CLAUDE_UI_PROMPT_RETRY_1__'+submission.proof);\n        send=findSendButton();\n        if(!send || !buttonSemanticState(send).ready) throw new Error('CLAUDE_SEND_BUTTON_NOT_READY_ON_RETRY');\n        send.focus();\n        send.click();\n        submission=await waitForSubmissionEstablished(bridgeRunId,envelope,turnBaseline,15000);\n      }\n\n      if(!submission.mode) throw new Error('CLAUDE_PROMPT_SUBMISSION_NOT_ESTABLISHED__'+submission.proof);\n      await progress(bridgeRunId,'CLAUDE_UI_PROMPT_SENT_CONFIRMED__PROOF020__'+submission.mode);\n      await waitForTurnAndGeneration(bridgeRunId,envelope,turnBaseline);\n'''
assert j.count(old_exec)==1, '018/019 execute submission anchor'
j=j.replace(old_exec,new_exec)
provider.write_text(j)
