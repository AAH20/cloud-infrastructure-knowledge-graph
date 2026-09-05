from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from dataclasses import asdict
from typing import Any, Iterable

from .model import Edge, Finding, Node


class GraphContractError(ValueError):
    pass


class InfrastructureGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.outgoing: dict[str, list[Edge]] = defaultdict(list)
        self.incoming: dict[str, list[Edge]] = defaultdict(list)

    def add_node(self, node: Node) -> None:
        existing = self.nodes.get(node.id)
        if existing and (existing.kind != node.kind or existing.name != node.name):
            raise GraphContractError(f"identity collision for {node.id}")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise GraphContractError(f"edge references missing node: {edge.source} -> {edge.target}")
        key = (edge.source, edge.target, edge.relation, edge.evidence)
        if any((item.source, item.target, item.relation, item.evidence) == key for item in self.edges):
            return
        self.edges.append(edge)
        self.outgoing[edge.source].append(edge)
        self.incoming[edge.target].append(edge)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "InfrastructureGraph":
        graph = cls()
        required = {"snapshot_id", "nodes", "edges"}
        if missing := required - payload.keys():
            raise GraphContractError(f"missing fields: {', '.join(sorted(missing))}")
        for raw in payload["nodes"]:
            graph.add_node(Node(**raw))
        for raw in payload["edges"]:
            graph.add_edge(Edge(**raw))
        return graph

    def traverse(self, start: str, direction: str = "both", max_depth: int = 5) -> dict[str, int]:
        if start not in self.nodes:
            raise GraphContractError(f"unknown node: {start}")
        if direction not in {"outgoing", "incoming", "both"}:
            raise GraphContractError("direction must be outgoing, incoming or both")
        distances = {start: 0}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            depth = distances[current]
            if depth >= max_depth:
                continue
            edges: Iterable[Edge]
            if direction == "outgoing":
                edges = self.outgoing[current]
            elif direction == "incoming":
                edges = self.incoming[current]
            else:
                edges = [*self.outgoing[current], *self.incoming[current]]
            for edge in edges:
                neighbor = edge.target if edge.source == current else edge.source
                if neighbor not in distances:
                    distances[neighbor] = depth + 1
                    queue.append(neighbor)
        return distances

    def blast_radius(self, failed_node: str, max_depth: int = 6) -> dict[str, Any]:
        impacted = self.traverse(failed_node, direction="incoming", max_depth=max_depth)
        impacted.pop(failed_node, None)
        business_services = []
        owners = set()
        monthly_revenue = 0.0
        for node_id, distance in impacted.items():
            node = self.nodes[node_id]
            if node.kind == "business_service":
                monthly_revenue += float(node.attributes.get("monthly_revenue_usd", 0))
                business_services.append({"id": node_id, "name": node.name, "distance": distance})
            if owner := node.attributes.get("owner"):
                owners.add(str(owner))
        business_services.sort(key=lambda row: (row["distance"], row["id"]))
        return {
            "failed_node": failed_node,
            "impacted_node_count": len(impacted),
            "impacted_business_services": business_services,
            "owners": sorted(owners),
            "modeled_monthly_revenue_exposure_usd": round(monthly_revenue, 2),
            "paths_are_observed_not_causal_proof": True,
        }

    def allocate_costs(self) -> dict[str, Any]:
        allocations: dict[str, float] = defaultdict(float)
        unallocated = 0.0
        for node in self.nodes.values():
            cost = float(node.attributes.get("monthly_cost_usd", 0))
            if cost <= 0:
                continue
            upstream = self.traverse(node.id, direction="incoming", max_depth=6)
            services = sorted(node_id for node_id in upstream if self.nodes[node_id].kind == "business_service")
            if not services:
                unallocated += cost
                continue
            share = cost / len(services)
            for service in services:
                allocations[service] += share
        return {
            "by_business_service_usd": {key: round(value, 2) for key, value in sorted(allocations.items())},
            "unallocated_usd": round(unallocated, 2),
            "allocation_method": "equal split across upstream business services in observed dependency graph",
        }

    def detect_drift(self) -> list[Finding]:
        findings: list[Finding] = []
        for node in self.nodes.values():
            declared = node.attributes.get("declared")
            observed = node.attributes.get("observed")
            if declared is not None and observed is not None and declared != observed:
                findings.append(Finding("DECLARED_OBSERVED_DRIFT", "high", node.id, f"declared state differs from observed state for {node.name}", [node.source]))
            if node.kind in {"azure_resource", "kubernetes_workload", "database"} and not node.attributes.get("owner"):
                findings.append(Finding("MISSING_OWNER", "medium", node.id, f"{node.name} has no accountable owner", [node.source]))
        findings.sort(key=lambda item: (item.severity, item.code, item.subject))
        return findings

    def integrity_report(self) -> dict[str, Any]:
        orphan_nodes = sorted(node_id for node_id in self.nodes if not self.incoming[node_id] and not self.outgoing[node_id])
        sources = sorted({node.source for node in self.nodes.values()})
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "orphan_nodes": orphan_nodes,
            "sources": sources,
            "owner_coverage_percent": round(100 * sum(bool(node.attributes.get("owner")) for node in self.nodes.values()) / max(len(self.nodes), 1), 2),
        }

    def evidence_digest(self) -> str:
        payload = {
            "nodes": [asdict(self.nodes[key]) for key in sorted(self.nodes)],
            "edges": [asdict(edge) for edge in sorted(self.edges, key=lambda item: (item.source, item.target, item.relation, item.evidence))],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(canonical).hexdigest()
