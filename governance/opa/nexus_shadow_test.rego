package nexus.shadow_test

import data.nexus.shadow

valid_input := {
    "schema": "NEXUS_OPA_SHADOW_INPUT_V1",
    "mode": "SHADOW_ONLY",
    "manifest": {
        "roadmap_workstream": "V-007",
        "candidate_classification": "UNVALIDATED_CANDIDATE",
        "affected_golden_paths": ["GP-1"],
        "required_components": ["COMP-1"],
        "change_scope": ["bounded delta"],
        "replay_plan": [{"golden_path_id": "GP-1", "required": true, "gate": "DEVICE replay"}],
        "baseline": {"file": "baseline.zip", "sha256": "abc"}
    },
    "expected_required_components": ["COMP-1"],
    "golden_observations": {"GP-1": {"exists": true, "registry_status": "ACTIVE_REFERENCE"}},
    "component_observations": {"COMP-1": {"exists": true, "status": "ACTIVE_REFERENCE", "sha256": "def"}},
    "baseline_observation": {"exists": true, "actual_sha256": "abc"}
}

test_valid_allows if {
    shadow.allow with input as valid_input
    ds := shadow.deny with input as valid_input
    count(ds) == 0
}

test_missing_baseline_denies if {
    mutated := object.union(valid_input, {"baseline_observation": {"exists": false, "actual_sha256": null}})
    not shadow.allow with input as mutated
    ds := shadow.deny with input as mutated
    "required frozen baseline missing" in ds
}

test_component_mismatch_denies if {
    manifest2 := object.union(valid_input.manifest, {"required_components": ["COMP-X"]})
    mutated := object.union(valid_input, {"manifest": manifest2})
    not shadow.allow with input as mutated
    ds := shadow.deny with input as mutated
    "required_components mismatch" in ds
}

test_missing_replay_denies if {
    manifest2 := object.union(valid_input.manifest, {"replay_plan": []})
    mutated := object.union(valid_input, {"manifest": manifest2})
    not shadow.allow with input as mutated
    ds := shadow.deny with input as mutated
    count(ds) > 0
}


test_empty_gate_denies if {
    manifest2 := object.union(valid_input.manifest, {"replay_plan": [{"golden_path_id": "GP-1", "required": true, "gate": ""}]})
    mutated := object.union(valid_input, {"manifest": manifest2})
    not shadow.allow with input as mutated
    ds := shadow.deny with input as mutated
    "each replay entry requires required=true and a non-empty gate" in ds
}
