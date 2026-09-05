from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    name: str
    source: str
    observed_at: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    evidence: str
    observed_at: str


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    subject: str
    message: str
    evidence: list[str]
