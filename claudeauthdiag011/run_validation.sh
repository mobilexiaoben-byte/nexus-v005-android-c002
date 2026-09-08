#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:?root required}"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
main=(root/'app/src/main/java/nexus/android/c002/MainActivity.kt').read_text()
claude=(root/'app/src/main/assets/nexus/claude_provider_c002.js').read_text()
gradle=(root/'app/build.gradle.kts').read_text()
manifest=(root/'app/src/main/AndroidManifest.xml').read_text()
checks=[]
def ok(name, cond):
    checks.append((name,bool(cond)))

ok('diag_application_id', 'applicationId = "nexus.android.c002.claudeauthdiagnostic011"' in gradle)
ok('diag_version_code', 'versionCode = 12' in gradle)
ok('diag_version_name', 'versionName = "0.0.12-c002-claude-authdiag011"' in gradle)
ok('diag_label', 'NEXUS C002 CLAUDE AUTH DIAGNOSTIC 011' in manifest)
ok('diag_profile', 'nexus_provider_profile_c002_claude_authdiag011' in main)
ok('diag_headline', 'CLAUDE AUTH DIAGNOSTIC 011 — NO JOB DISPATCHED' in main)
ok('snapshot_event', 'CLAUDE_AUTH_SNAPSHOT' in main)
ok('snapshot_body', 'MAX_DIAGNOSTIC_BODY_CHARS = 6000' in main)
handle=main.split('private fun handleStatus',1)[1].split('private fun startExecutionProof',1)[0]
ok('handle_no_execution_call', 'startExecutionProof(' not in handle and 'EXECUTE_JOB' not in handle)
ok('provider_diagnostic_snapshot', 'diagnostic:diagnosticSnapshot()' in claude)
ok('provider_structure_only', 'visible_inputs:inputs' in claude and 'auth_token_hits' in claude)
ok('provider_execute_blocked', "CLAUDE_AUTH_DIAGNOSTIC_011_NO_EXECUTION" in claude)
ok('provider_execute_not_invoked', 'setTimeout(()=>executeJob' not in claude)
ok('origin_exact', 'const val CLAUDE_ORIGIN = "https://claude.ai"' in main)
ok('transport_preserved', 'const val TRANSPORT_ID = "ANDROID_WEBVIEW_CHROMIUM_BRIDGE"' in main)
ok('no_chatgpt_controller_route', 'SelectedProvider.CHATGPT' not in main and 'CHATGPT_ORIGIN' not in main)
for name,passed in checks:
    print(('PASS' if passed else 'FAIL')+' '+name)
failed=[n for n,p in checks if not p]
print(f'CLAUDE_AUTH_DIAGNOSTIC_011_STATIC_RESULT pass={len(checks)-len(failed)} fail={len(failed)}')
if failed:
    raise SystemExit('failed: '+','.join(failed))
PY
