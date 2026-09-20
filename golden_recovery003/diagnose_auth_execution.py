#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1])
files=list(root.rglob("*.kt"))+list(root.rglob("*.js"))
needles=[
 "ANDROID_DUPLICATE_EXECUTION_ID",
 "DUPLICATE_EXECUTION",
 "JOB_ID",
 "manualProviderConfirmationMode",
 "providerConfirmedByUser",
 "productRunRequested",
 "executionStarted",
 "proofStopped",
 "buildJob(",
 "requestId",
 "seenExecution",
 "seenRequest",
]
for path in files:
    text=path.read_text(errors="ignore")
    hits=[]
    for needle in needles:
        for m in re.finditer(re.escape(needle), text, re.I):
            hits.append((m.start(),needle))
    if not hits: continue
    print("\n######## FILE",path.relative_to(root),"########")
    printed=[]
    for pos,needle in sorted(hits)[:60]:
        a=max(0,pos-1400); b=min(len(text),pos+2600)
        if any(abs(a-x)<600 for x in printed): continue
        printed.append(a)
        print("\n===== MATCH",needle,"AT",pos,"=====\n")
        print(text[a:b])
