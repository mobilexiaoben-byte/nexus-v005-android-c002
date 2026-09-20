#!/usr/bin/env python3
import copy, json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / "governance" / "preflight" / "android-provider-runtime.json"
OPA = ROOT / "governance" / "opa" / "nexus_shadow.rego"
EXPORTER = ROOT / "governance" / "opa" / "export_preflight_input.py"
GUARD = ROOT / "governance" / "golden_guard.py"

base = json.loads(BASE.read_text(encoding="utf-8"))

def mutate(name):
    m = copy.deepcopy(base)
    if name == "valid":
        pass
    elif name == "bad_classification":
        m["candidate_classification"] = "CERTIFIED"
    elif name == "missing_baseline_file":
        m["baseline"]["file"] = "DOES_NOT_EXIST.zip"
    elif name == "bad_baseline_hash":
        m["baseline"]["sha256"] = "0" * 64
    elif name == "empty_goldens":
        m["affected_golden_paths"] = []
        m["required_components"] = []
        m["replay_plan"] = []
    elif name == "empty_change_scope":
        m["change_scope"] = []
    elif name == "unknown_golden":
        m["affected_golden_paths"] = ["GP-UNKNOWN"]
        m["required_components"] = []
        m["replay_plan"] = [{"golden_path_id":"GP-UNKNOWN","required":True,"gate":"DEVICE replay"}]
    elif name == "component_mismatch":
        m["required_components"] = m["required_components"][:-1]
    elif name == "missing_replay":
        m["replay_plan"] = m["replay_plan"][:-1]
    elif name == "replay_not_required":
        m["replay_plan"][0]["required"] = False
    elif name == "replay_empty_gate":
        m["replay_plan"][0]["gate"] = ""
    elif name == "missing_required_key":
        del m["change_scope"]
    else:
        raise ValueError(name)
    return m

cases = [
    "valid",
    "bad_classification",
    "missing_baseline_file",
    "bad_baseline_hash",
    "empty_goldens",
    "empty_change_scope",
    "unknown_golden",
    "component_mismatch",
    "missing_replay",
    "replay_not_required",
    "replay_empty_gate",
    "missing_required_key",
]

rows=[]
with tempfile.TemporaryDirectory(dir=ROOT / "governance" / "opa") as td:
    td=pathlib.Path(td)
    for name in cases:
        manifest=td / f"{name}.json"
        inp=td / f"{name}.input.json"
        manifest.write_text(json.dumps(mutate(name), indent=2)+"\n", encoding="utf-8")
        rel_manifest=manifest.relative_to(ROOT)
        rel_inp=inp.relative_to(ROOT)

        g=subprocess.run([sys.executable, str(GUARD), "--manifest", str(rel_manifest)], cwd=ROOT, text=True, capture_output=True)
        guard_allow=(g.returncode==0)

        e=subprocess.run([sys.executable, str(EXPORTER), "--manifest", str(rel_manifest), "--output", str(rel_inp)], cwd=ROOT, text=True, capture_output=True)
        if e.returncode != 0:
            opa_allow=False
            opa_error="exporter_failed: "+e.stderr.strip()
        else:
            o=subprocess.run(["opa","eval","--format","json","--data",str(OPA),"--input",str(inp),"data.nexus.shadow.allow"], cwd=ROOT, text=True, capture_output=True)
            if o.returncode != 0:
                opa_allow=False
                opa_error="opa_failed: "+o.stderr.strip()
            else:
                doc=json.loads(o.stdout)
                results=doc.get("result",[])
                if not results:
                    opa_allow=False
                else:
                    opa_allow=bool(results[0].get("expressions",[{}])[0].get("value",False))
                opa_error=""

        parity=(guard_allow==opa_allow)
        rows.append({"case":name,"golden_guard_allow":guard_allow,"opa_allow":opa_allow,"parity":parity,"guard_stderr":g.stderr.strip(),"opa_error":opa_error})
        print(f"{name}: guard={guard_allow} opa={opa_allow} parity={'PASS' if parity else 'MISMATCH'}")

print(json.dumps(rows, indent=2))
bad=[r for r in rows if not r["parity"]]
if bad:
    print(f"NEXUS_OPA_SHADOW_CORPUS_PARITY=MISMATCH count={len(bad)}", file=sys.stderr)
    raise SystemExit(1)
print(f"NEXUS_OPA_SHADOW_CORPUS_PARITY=PASS cases={len(rows)}")
