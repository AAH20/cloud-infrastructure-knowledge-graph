# Production architecture

Collectors publish source observations into an append-only ingestion boundary. A normalizer converts provider-specific data into versioned ontology records. Identity resolution maps observations to stable entities while preserving source IDs and timestamps. Graph storage serves deterministic queries; a separately governed vector index supports explanatory retrieval.

Production invariants:

- source observations are immutable and timestamped;
- normalized nodes retain source provenance;
- inferred edges are visibly different from observed edges;
- identity merges are reversible and audited;
- tenant graphs and encryption keys are isolated;
- queries are bounded by tenant and relationship authorization;
- GraphRAG cannot create authoritative relationships;
- external changes require plan, approval and post-change observation;
- deletion follows retention and legal-hold policy;
- integrity digests do not claim non-repudiation without authenticated signing and evidence custody.

Recommended components include OpenTelemetry Collector-style connectors, a durable event stream, PostgreSQL/Apache AGE or Neo4j, object storage for source evidence, OpenCypher APIs, OpenCost and an OPA/Cedar authorization layer.
