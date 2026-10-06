from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Agent:
    name: str
    role: str
    capability: str
    status: str = "waiting"
    last_action: str = "Waiting for a case"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Event:
    id: str
    actor: str
    role: str
    kind: str
    message: str
    recipient: str | None = None
    artifact: str | None = None
    level: str = "info"
    execution: bool = False
    timestamp: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Artifact:
    name: str
    kind: str
    description: str
    content: str
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Run:
    id: str
    task: str
    mode: str
    status: str
    created_at: str
    updated_at: str
    agents: list[Agent]
    events: list[Event] = field(default_factory=list)
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    human_gate: str = "not_ready"
    report: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agents": [agent.to_dict() for agent in self.agents],
            "events": [event.to_dict() for event in self.events],
            "artifacts": {key: value.to_dict() for key, value in self.artifacts.items()},
            "metrics": self.metrics,
            "human_gate": self.human_gate,
            "report": self.report,
        }
