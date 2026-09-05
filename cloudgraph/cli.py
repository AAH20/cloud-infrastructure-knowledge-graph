from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyze import analyze_snapshot
from .graph import GraphContractError
from .render import write_outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze an infrastructure knowledge-graph snapshot")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--failed-node", required=True)
    parser.add_argument("--output", type=Path, default=Path("generated"))
    args = parser.parse_args()
    try:
        payload = json.loads(args.snapshot.read_text())
        result = analyze_snapshot(payload, args.failed_node)
    except (OSError, json.JSONDecodeError, GraphContractError) as exc:
        parser.error(str(exc))
    write_outputs(payload, result, args.output)
    print(json.dumps({"snapshot_id": result["snapshot_id"], "evidence_digest": result["evidence_digest"], "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
