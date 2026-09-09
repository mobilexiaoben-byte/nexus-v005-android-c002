from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/'app/src/main/java/nexus/android/c002/MainActivity.kt'
s=p.read_text()
for marker in ['MODE=','RUN=','PRIOR_PHASE=','PHASE=','EXECUTE_JOB=','PROMPT_INJECTION=']:
    broken='append("\n'+marker
    fixed='append("\\n'+marker
    assert s.count(broken)==1, marker
    s=s.replace(broken,fixed,1)
p.write_text(s)
