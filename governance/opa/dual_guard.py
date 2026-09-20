#!/usr/bin/env python3
import argparse, json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUARD = ROOT / "governance" / "golden_guard.py"
EXPORTER = ROOT / "governance" / "opa" / "export_preflight_input.py"
POLICY = ROOT / "governance" / "opa" / "nexus_shadow.rego"

def fail(msg):
    print("NEXUS_OPA_DUAL_ENFORCEMENT=FAIL", file=sys.stderr)
    print(msg, file=sys.stderr)
    raise SystemExit(2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    guard = subprocess.run(
        [sys.executable, str(GUARD), "--manifest", args.manifest],
        cwd=ROOT, text=True, capture_output=True
    )
    print(guard.stdout, end="")
    if guard.returncode != 0:
        if guard.stderr:
            print(guard.stderr, end="", file=sys.stderr)
        fail("existing golden_guard.py denied candidate")

    with tempfile.TemporaryDirectory(dir=ROOT / "governance" / "opa") as td:
        out = pathlib.Path(td) / "input.json"
        rel_out = out.relative_to(ROOT)
        exp = subprocess.run(
            [sys.executable, str(EXPORTER), "--manifest", args.manifest, "--output", str(rel_out)],
            cwd=ROOT, text=True, capture_output=True
        )
        if exp.returncode != 0:
            fail("OPA input export failed: " + exp.stderr.strip())

        opa = subprocess.run(
            ["opa", "eval", "--format", "json", "--data", str(POLICY),
             "--input", str(out), "data.nexus.shadow.decision"],
            cwd=ROOT, text=True, capture_output=True
        )
        if opa.returncode != 0:
            fail("OPA evaluation failed: " + opa.stderr.strip())
        try:
            doc = json.loads(opa.stdout)
            decision = doc["result"][0]["expressions"][0]["value"]
        except Exception as exc:
            fail(f"OPA decision parse failed: {exc}")
        if decision.get("allow") is not True or decision.get("deny"):
            fail("OPA denied candidate: " + json.dumps(decision, sort_keys=True))

    print("NEXUS_OPA_DUAL_ENFORCEMENT=PASS")
    print("GOLDEN_GUARD=PASS")
    print("OPA=PASS")

if __name__ == "__main__":
    main()
