from pathlib import Path
import sys

repo = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()

# Build on the exact DEVICE-tested 009 candidate.
exec((repo / "reconcile009" / "provider_runtime_009.py").read_text(), {
    "__name__": "__main__",
    "__file__": str(repo / "reconcile009" / "provider_runtime_009.py"),
    "sys": sys,
})

assets = root / "app/src/main/assets/nexus"

# 009 inserted a literal backslash+n before console.info. That makes the generated
# provider adapter invalid JavaScript, so it never reaches NexusNativeC002 and
# replyByOrigin can never materialize. Replace that malformed suffix with a real
# newline and bounded BRIDGE_READY retries.
for name in ["chatgpt_provider_c002.js", "gemini_provider_c002.js", "zai_provider_c002.js"]:
    p = assets / name
    js = p.read_text()
    malformed = "nativeSend({channel:CHANNEL,type:'BRIDGE_READY'}).catch(()=>{});\\n  console.info("
    assert malformed in js, f"009 malformed BRIDGE_READY suffix missing in {name}"
    ready = (
        "[0,100,300,1000].forEach((delay)=>setTimeout(()=>{"
        "nativeSend({channel:CHANNEL,type:'BRIDGE_READY'}).catch(()=>{});"
        "},delay));\n  console.info("
    )
    js = js.replace(malformed, ready, 1)
    p.write_text(js)

# Candidate identity.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text()
assert "versionCode = 63" in g
assert 'versionName = "0.0.63-v007-m024-u013-provider-runtime009"' in g
g = g.replace("versionCode = 63", "versionCode = 64", 1)
g = g.replace(
    'versionName = "0.0.63-v007-m024-u013-provider-runtime009"',
    'versionName = "0.0.64-v007-m024-u013-provider-runtime010"',
    1
)
gradle.write_text(g)

lock = root / "RECONCILIATION_LOCK.txt"
lock.write_text(lock.read_text() +
    "PROVIDER_RUNTIME010_ROOT_CAUSE=009_BRIDGE_READY_LITERAL_BACKSLASH_N_JS_SYNTAX_BREAK\n"
    "PROVIDER_RUNTIME010_BRIDGE_READY=VALID_JS_BOUNDED_RETRY_0_100_300_1000MS\n"
    "PROVIDER_RUNTIME010_JS_SYNTAX_GATE=NODE_CHECK_REQUIRED\n"
    "FACTCHECK010_USER_TOKEN_UI=ABSENT\n"
    "FACTCHECK010_SERVER_RESULT=UNAUTHORIZED_DEVICE_EVIDENCE_PENDING_BACKEND_AUTH_FIX\n"
    "DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

# Static invariants.
for name in ["chatgpt_provider_c002.js", "gemini_provider_c002.js", "zai_provider_c002.js"]:
    js = (assets / name).read_text()
    assert "type:'BRIDGE_READY'" in js, name
    assert "\\n  console.info(" not in js, name
    assert "[0,100,300,1000].forEach" in js, name
