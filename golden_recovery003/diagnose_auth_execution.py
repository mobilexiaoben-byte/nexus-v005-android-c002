#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1])
main=root/"app/src/main/java/nexus/android/c002/MainActivity.kt"
text=main.read_text()
needles=[
 "ANDROID_DUPLICATE_EXECUTION_ID",
 "executionId",
 "execution_id",
 "AUTH: UNKNOWN",
 "AUTH_UNKNOWN",
 "Connexion à",
 "authenticated",
 "connected",
 "providerState",
 "authState",
 "startExecutionProof",
]
seen=set()
for needle in needles:
    for m in re.finditer(re.escape(needle), text, re.I):
        a=max(0,m.start()-1800); b=min(len(text),m.end()+3200)
        key=(a,b)
        if key in seen: continue
        seen.add(key)
        print("\n===== MATCH",needle,"AT",m.start(),"=====\n")
        print(text[a:b])
print("\n===== END DIAGNOSTIC =====")
