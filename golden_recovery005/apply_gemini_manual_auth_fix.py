from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
gem = root / "app/src/main/assets/nexus/gemini_provider_c002.js"
gradle = root / "app/build.gradle.kts"
lock = root / "RECONCILIATION_LOCK.txt"

g = gem.read_text()

old = """      const auth=detectAuth();
      if(auth.state!=='AUTHENTICATED') throw new Error('GEMINI_NOT_AUTHENTICATED:'+auth.state);
"""
new = """      const observedAuth=detectAuth();
      const userConfirmed=(envelope.user_confirmed_connected===true);
      const auth=userConfirmed
        ? {...observedAuth,state:'AUTHENTICATED',reason:'USER_CONFIRMED_CONNECTED__'+String(observedAuth.state||'UNKNOWN')}
        : observedAuth;
      if(auth.state!=='AUTHENTICATED') throw new Error('GEMINI_NOT_AUTHENTICATED:'+auth.state);
"""
assert old in g, "Gemini auth gate anchor missing"
g = g.replace(old, new, 1)
gem.write_text(g)

b = gradle.read_text()
assert "versionCode = 76" in b
assert 'versionName = "0.0.76-v007-golden-recovery004-golden-diff-fix"' in b
b = b.replace("versionCode = 76", "versionCode = 77", 1)
b = b.replace(
    'versionName = "0.0.76-v007-golden-recovery004-golden-diff-fix"',
    'versionName = "0.0.77-v007-golden-recovery005-gemini-manual-auth-fix"',
    1
)
gradle.write_text(b)

lock.write_text(lock.read_text() +
    "GOLDEN_RECOVERY005_GEMINI_AUTH=USER_CONFIRMED_CONNECTED_CONSUMED_AFTER_NATIVE_ORIGIN_GUARD\n"
    "GOLDEN_RECOVERY005_GEMINI_AUTO_LOGIN=NOT_ADDED\n"
    "GOLDEN_RECOVERY005_GEMINI_TRANSPORT=UNCHANGED\n"
    "GOLDEN_RECOVERY005_GEMINI_CAPTURE=UNCHANGED\n"
    "GOLDEN_RECOVERY005_M024_POLICY=UNCHANGED\n"
    "GOLDEN_RECOVERY005_DEVICE_PASS=NOT_YET_ACQUIRED\n"
)

out = gem.read_text()
assert "user_confirmed_connected===true" in out
assert "USER_CONFIRMED_CONNECTED__" in out
assert "GEMINI_NOT_AUTHENTICATED" in out
assert "GEMINI_UI_PROMPT_SENT_CONFIRMED" in out
assert "waitForModelResult(bridgeRunId,beforeSnapshot,envelope)" in out
