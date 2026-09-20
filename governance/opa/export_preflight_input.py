#!/usr/bin/env python3
import argparse, hashlib, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "governance" / "golden_registry_snapshot.json"

def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    manifest_path = (ROOT / args.manifest).resolve()
    if ROOT not in manifest_path.parents or not manifest_path.exists():
        raise SystemExit(f"invalid or missing manifest: {args.manifest}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    expected_components = set()
    golden_observations = {}
    for gid in manifest.get("affected_golden_paths", []):
        g = registry.get("golden_paths", {}).get(gid)
        golden_observations[gid] = {
            "exists": g is not None,
            "registry_status": None if g is None else g.get("registry_status"),
        }
        if g:
            expected_components.update(g.get("component_ids", []))

    component_observations = {}
    for cid in manifest.get("required_components", []):
        c = registry.get("components", {}).get(cid)
        component_observations[cid] = {
            "exists": c is not None,
            "status": None if c is None else c.get("status"),
            "sha256": None if c is None else c.get("sha256"),
        }

    baseline = manifest.get("baseline")
    baseline_obs = {"exists": False, "actual_sha256": None}
    if isinstance(baseline, dict) and baseline.get("file"):
        bp = (ROOT / baseline["file"]).resolve()
        if ROOT in bp.parents and bp.exists() and bp.is_file():
            baseline_obs = {"exists": True, "actual_sha256": sha256_file(bp)}

    payload = {
        "schema": "NEXUS_OPA_SHADOW_INPUT_V1",
        "mode": "SHADOW_ONLY",
        "manifest": manifest,
        "expected_required_components": sorted(expected_components),
        "golden_observations": golden_observations,
        "component_observations": component_observations,
        "baseline_observation": baseline_obs,
    }
    out = (ROOT / args.output).resolve()
    if ROOT not in out.parents:
        raise SystemExit("output path escapes repository")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT))

if __name__ == "__main__":
    main()
