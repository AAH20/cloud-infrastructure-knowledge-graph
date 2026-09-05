# Security policy

Do not submit production topology, credentials, tokens, customer records or confidential infrastructure evidence in a public issue. Report suspected vulnerabilities privately through GitHub's security-advisory workflow.

The offline reference engine performs no network calls and makes no infrastructure changes. Future collectors and query services must enforce tenant isolation, least-privilege read scopes, bounded traversal, evidence retention policy and relationship-level authorization. Treat imported graph records, labels and GraphRAG context as untrusted data.

Before production use, complete threat modeling, dependency scanning, provenance signing, backup and restore tests, access reviews and an authorized penetration test.
