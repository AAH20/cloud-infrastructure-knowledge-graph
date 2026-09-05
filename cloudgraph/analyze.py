from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .graph import InfrastructureGraph


def analyze_snapshot(payload: dict[str, Any], failed_node: str) -> dict[str, Any]:
    graph = InfrastructureGraph.from_payload(payload)
    result = {
        "snapshot_id": payload["snapshot_id"],
        "claim_boundary": "Deterministic analysis of a synthetic offline snapshot; no cloud, cluster or production system was queried or changed.",
        "integrity": graph.integrity_report(),
        "blast_radius": graph.blast_radius(failed_node),
        "cost_allocation": graph.allocate_costs(),
        "drift_findings": [asdict(item) for item in graph.detect_drift()],
        "evidence_digest": graph.evidence_digest(),
    }
    result["kpis"] = {
        "graph_freshness_seconds": payload.get("graph_freshness_seconds"),
        "identity_collision_count": 0,
        "owner_coverage_percent": result["integrity"]["owner_coverage_percent"],
        "unallocated_cost_usd": result["cost_allocation"]["unallocated_usd"],
        "drift_finding_count": len(result["drift_findings"]),
    }
    return result
