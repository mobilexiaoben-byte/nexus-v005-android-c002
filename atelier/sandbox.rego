package nexus.atelier.sandbox

import rego.v1

default allow := false

base if {
    input.mode == "SANDBOX_ONLY"
    input.schema_valid == true
    input.authority_fresh == true
    input.authority_conflict == false
    input.candidate_match == true
}

ready if {
    input.baseline_verified == true
    input.components_verified == true
    input.evidence_verified == true
    input.workstream_mutation_enabled == true
    input.workstream_closed == false
}

allow if {
    base
    input.action == "inspect"
    input.role in {"agent", "reviewer"}
}

allow if {
    base
    ready
    input.action == "preflight"
    input.role == "agent"
    input.state == "DRAFT"
}

allow if {
    base
    ready
    input.action == "approve"
    input.role == "reviewer"
    input.state == "CHECKED"
}

allow if {
    base
    ready
    input.action == "release"
    input.role == "agent"
    input.state == "APPROVED"
}

# No delete/production/shell/model-controlled proof or role.
decision := {"allow": allow, "scope": "SANDBOX_ONLY"}
