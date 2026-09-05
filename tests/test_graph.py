import copy
import json
import unittest
from pathlib import Path

from cloudgraph.analyze import analyze_snapshot
from cloudgraph.graph import GraphContractError, InfrastructureGraph


FIXTURE = Path(__file__).parents[1] / "examples" / "azure-aks-commerce-snapshot.json"


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text())

    def test_blast_radius_reaches_business_service(self):
        result = analyze_snapshot(self.payload, "azure:private-dns-postgres")
        services = result["blast_radius"]["impacted_business_services"]
        self.assertEqual(services[0]["id"], "business:checkout")
        self.assertEqual(result["blast_radius"]["modeled_monthly_revenue_exposure_usd"], 420000)

    def test_cost_is_allocated_and_orphan_remains_unallocated(self):
        result = analyze_snapshot(self.payload, "azure:postgres-orders")
        self.assertEqual(result["cost_allocation"]["unallocated_usd"], 96)
        self.assertGreater(result["cost_allocation"]["by_business_service_usd"]["business:checkout"], 0)

    def test_detects_declared_observed_drift_and_missing_owner(self):
        result = analyze_snapshot(self.payload, "k8s:prod/checkout")
        codes = [item["code"] for item in result["drift_findings"]]
        self.assertIn("DECLARED_OBSERVED_DRIFT", codes)
        self.assertIn("MISSING_OWNER", codes)

    def test_orphan_is_reported(self):
        graph = InfrastructureGraph.from_payload(self.payload)
        self.assertEqual(graph.integrity_report()["orphan_nodes"], ["orphan:disk-17"])

    def test_rejects_edge_to_unknown_node(self):
        payload = copy.deepcopy(self.payload)
        payload["edges"][0]["target"] = "missing"
        with self.assertRaisesRegex(GraphContractError, "missing node"):
            InfrastructureGraph.from_payload(payload)

    def test_identity_collision_is_rejected(self):
        payload = copy.deepcopy(self.payload)
        duplicate = copy.deepcopy(payload["nodes"][0])
        duplicate["kind"] = "database"
        payload["nodes"].append(duplicate)
        with self.assertRaisesRegex(GraphContractError, "identity collision"):
            InfrastructureGraph.from_payload(payload)

    def test_digest_is_deterministic(self):
        first = InfrastructureGraph.from_payload(self.payload).evidence_digest()
        second = InfrastructureGraph.from_payload(self.payload).evidence_digest()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
