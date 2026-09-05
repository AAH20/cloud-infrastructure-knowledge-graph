# Ontology and identity

The first ontology covers `business_service`, `application`, `kubernetes_workload`, `azure_resource`, `database`, `managed_identity` and `iac_module`. Relations include `depends_on`, `runs_as`, `runs_on`, `calls`, `exposed_by`, `resolves_through`, `authenticates_as`, `can_access` and `declares`.

Stable identity is harder than storage. A production resolver must preserve every native identifier, cloud scope, tenant, environment, namespace and validity interval. Name equality alone must never merge resources. Ambiguous candidates remain separate until a deterministic rule or authorized review resolves them.

Edges require provenance, observation time and confidence. Direct provider configuration, runtime telemetry, IaC declarations and model inference are different evidence types and must not be silently combined.
