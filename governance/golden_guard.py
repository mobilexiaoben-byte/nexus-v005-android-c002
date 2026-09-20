#!/usr/bin/env python3
import argparse, hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "governance" / "golden_registry_snapshot.json"

def fail(msg):
    print("NEXUS_GOVERNANCE_PREFLIGHT=FAIL", file=sys.stderr)
    print(msg, file=sys.stderr)
    raise SystemExit(2)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args=ap.parse_args()
    reg=json.loads(REGISTRY.read_text(encoding="utf-8"))
    p=(ROOT / args.manifest).resolve()
    if ROOT not in p.parents:
        fail("manifest path escapes repository")
    if not p.exists():
        fail(f"missing preflight manifest: {args.manifest}")
    m=json.loads(p.read_text(encoding="utf-8"))

    required=["roadmap_workstream","candidate_classification","affected_golden_paths","required_components","change_scope","replay_plan","baseline"]
    missing=[k for k in required if k not in m]
    if missing: fail("missing keys: "+",".join(missing))
    if m["candidate_classification"]!="UNVALIDATED_CANDIDATE":
        fail("candidate_classification must be UNVALIDATED_CANDIDATE")
    baseline=m["baseline"]
    if not isinstance(baseline,dict) or not baseline.get("file") or not baseline.get("sha256"):
        fail("baseline.file and baseline.sha256 are required")
    bp=(ROOT / baseline["file"]).resolve()
    if ROOT not in bp.parents or not bp.exists():
        fail(f"required frozen baseline missing: {baseline.get('file')}")
    h=hashlib.sha256()
    with bp.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            h.update(chunk)
    got=h.hexdigest()
    if got != baseline["sha256"]:
        fail(f"baseline SHA256 mismatch: expected={baseline['sha256']} actual={got}")
    if not isinstance(m["affected_golden_paths"],list) or not m["affected_golden_paths"]:
        fail("affected_golden_paths must be non-empty")
    if not isinstance(m["change_scope"],list) or not m["change_scope"]:
        fail("change_scope must be non-empty")

    expected=set()
    for gid in m["affected_golden_paths"]:
        g=reg["golden_paths"].get(gid)
        if not g or g.get("registry_status")!="ACTIVE_REFERENCE":
            fail(f"unknown/non-active Golden Path: {gid}")
        expected.update(g.get("component_ids",[]))
    actual=set(m["required_components"])
    if actual != expected:
        fail(f"required_components mismatch: expected={sorted(expected)} actual={sorted(actual)}")
    for cid in actual:
        c=reg["components"].get(cid)
        if not c or c.get("status") not in {"ACTIVE_REFERENCE","ACTIVE_REFERENCE_GAP","ACTIVE_REQUIRED_REPLAY"}:
            fail(f"component not protected/current: {cid}")

    replay=m["replay_plan"]
    if not isinstance(replay,list):
        fail("replay_plan must be a list")
    replay_ids={x.get("golden_path_id") for x in replay if isinstance(x,dict)}
    missing_replay=set(m["affected_golden_paths"])-replay_ids
    if missing_replay:
        fail("missing replay plan for: "+",".join(sorted(missing_replay)))
    for x in replay:
        if not isinstance(x,dict) or x.get("required") is not True or not x.get("gate"):
            fail("each replay entry requires required=true and a non-empty gate")

    print("NEXUS_GOVERNANCE_PREFLIGHT=PASS")
    print("WORKSTREAM="+str(m["roadmap_workstream"]))
    print("GOLDENS="+",".join(m["affected_golden_paths"]))
    print("COMPONENTS="+",".join(sorted(actual)))

if __name__=="__main__":
    main()
