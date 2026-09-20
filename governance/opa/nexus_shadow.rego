package nexus.shadow

default allow := false

required_manifest_keys := {
    "roadmap_workstream",
    "candidate_classification",
    "affected_golden_paths",
    "required_components",
    "change_scope",
    "replay_plan",
    "baseline",
}

protected_component_statuses := {
    "ACTIVE_REFERENCE",
    "ACTIVE_REFERENCE_GAP",
    "ACTIVE_REQUIRED_REPLAY",
}

deny contains msg if {
    missing := required_manifest_keys - object.keys(input.manifest)
    count(missing) > 0
    msg := sprintf("missing keys: %s", [concat(",", sort([x | some x in missing]))])
}

deny contains "candidate_classification must be UNVALIDATED_CANDIDATE" if {
    input.manifest.candidate_classification != "UNVALIDATED_CANDIDATE"
}

deny contains "affected_golden_paths must be non-empty" if {
    count(input.manifest.affected_golden_paths) == 0
}

deny contains "change_scope must be non-empty" if {
    count(input.manifest.change_scope) == 0
}

deny contains "baseline.file and baseline.sha256 are required" if {
    not input.manifest.baseline.file
}

deny contains "baseline.file and baseline.sha256 are required" if {
    not input.manifest.baseline.sha256
}

deny contains "required frozen baseline missing" if {
    not input.baseline_observation.exists
}

deny contains "baseline SHA256 mismatch" if {
    input.baseline_observation.exists
    input.baseline_observation.actual_sha256 != input.manifest.baseline.sha256
}

deny contains msg if {
    some gid in input.manifest.affected_golden_paths
    obs := input.golden_observations[gid]
    not obs.exists
    msg := sprintf("unknown/non-active Golden Path: %s", [gid])
}

deny contains msg if {
    some gid in input.manifest.affected_golden_paths
    obs := input.golden_observations[gid]
    obs.exists
    obs.registry_status != "ACTIVE_REFERENCE"
    msg := sprintf("unknown/non-active Golden Path: %s", [gid])
}

deny contains "required_components mismatch" if {
    actual := {x | some x in input.manifest.required_components}
    expected := {x | some x in input.expected_required_components}
    actual != expected
}

deny contains msg if {
    some cid in input.manifest.required_components
    obs := input.component_observations[cid]
    not obs.exists
    msg := sprintf("component not protected/current: %s", [cid])
}

deny contains msg if {
    some cid in input.manifest.required_components
    obs := input.component_observations[cid]
    obs.exists
    not obs.status in protected_component_statuses
    msg := sprintf("component not protected/current: %s", [cid])
}

replay_ids := {x.golden_path_id | some x in input.manifest.replay_plan}

deny contains msg if {
    some gid in input.manifest.affected_golden_paths
    not gid in replay_ids
    msg := sprintf("missing replay plan for: %s", [gid])
}

deny contains "each replay entry requires required=true and a non-empty gate" if {
    some x in input.manifest.replay_plan
    x.required != true
}

deny contains "each replay entry requires required=true and a non-empty gate" if {
    some x in input.manifest.replay_plan
    not x.gate
}

deny contains "each replay entry requires required=true and a non-empty gate" if {
    some x in input.manifest.replay_plan
    x.gate == ""
}

allow if {
    count(deny) == 0
}

decision := {
    "allow": allow,
    "deny": sort([x | some x in deny]),
    "mode": "SHADOW_ONLY",
    "schema": "NEXUS_OPA_SHADOW_DECISION_V1",
}
