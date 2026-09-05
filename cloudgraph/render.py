from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_report(result: dict[str, Any]) -> str:
    blast = result["blast_radius"]
    services = "\n".join(f"- {row['name']} (`{row['id']}`), graph distance {row['distance']}" for row in blast["impacted_business_services"]) or "- None found"
    findings = "\n".join(f"- **{row['severity'].upper()}** `{row['code']}` — {row['message']}" for row in result["drift_findings"]) or "- None"
    allocations = "\n".join(f"| `{service}` | ${cost:,.2f} |" for service, cost in result["cost_allocation"]["by_business_service_usd"].items())
    return f"""# CloudGraph evidence report

Snapshot: `{result['snapshot_id']}`
Evidence digest: `{result['evidence_digest']}`

## Blast-radius analysis

Starting node: `{blast['failed_node']}`

- Impacted graph nodes: {blast['impacted_node_count']}
- Modeled monthly revenue exposure: ${blast['modeled_monthly_revenue_exposure_usd']:,.2f}
- Owners to engage: {', '.join(blast['owners'])}

### Impacted business services

{services}

Observed graph paths show potential dependency exposure; they do not prove that the starting node caused an incident.

## Cost allocation

| Business service | Allocated monthly cost |
|---|---:|
{allocations}

Unallocated: ${result['cost_allocation']['unallocated_usd']:,.2f}

Method: {result['cost_allocation']['allocation_method']}.

## Drift and ownership findings

{findings}

## Evidence boundary

{result['claim_boundary']}
"""


def render_mermaid(payload: dict[str, Any]) -> str:
    lines = ["flowchart LR"]
    for node in sorted(payload["nodes"], key=lambda item: item["id"]):
        safe_id = node["id"].replace(":", "_").replace("-", "_").replace("/", "_")
        label = f"{node['kind']}\\n{node['name']}".replace('"', "'")
        lines.append(f'  {safe_id}["{label}"]')
    for edge in sorted(payload["edges"], key=lambda item: (item["source"], item["target"], item["relation"])):
        source = edge["source"].replace(":", "_").replace("-", "_").replace("/", "_")
        target = edge["target"].replace(":", "_").replace("-", "_").replace("/", "_")
        lines.append(f"  {source} -->|{edge['relation']}| {target}")
    return "```mermaid\n" + "\n".join(lines) + "\n```\n"


def write_outputs(payload: dict[str, Any], result: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "evidence-report.md").write_text(render_report(result))
    (output / "topology.md").write_text("# Observed topology\n\n" + render_mermaid(payload))
