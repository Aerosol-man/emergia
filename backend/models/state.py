# backend/models/state.py
from __future__ import annotations
from typing import Dict, List, Tuple
from dataclasses import dataclass

from .agent import Agent

print("DEBUG: LOADING backend/models/state.py")

class SimulationState:
    def __init__(
        self,
        num_agents: int,
        trust_decay: float,
        trust_quota: float,
        bounds: Tuple[float, float] = (1000.0, 1000.0),
        max_speed: float = 50.0,
    ):
        self.agents: Dict[int, Agent] = {}
        self.agent_count: int = 0
        self.tick: int = 0

        # config
        self.trust_decay: float = float(trust_decay)     # 0..1 interpreted as "per-decay-step loss"
        self.trust_quota: float = float(trust_quota)
        self.bounds: Tuple[float, float] = bounds
        self.max_speed: float = max_speed

        # global trust params (used by trust engine)
        self.global_alpha: float = 0.10  # trust up step
        self.global_beta: float = 0.05   # trust down step

        # logs
        self.collision_log: List[dict] = []
        self.events: List[dict] = []

        # metrics
        self.metrics: dict = {
            "avgTrust": 0.0,
            "giniCoefficient": 0.0,
            "tradeSuccessRate": 0.0,
            "tradeCount": 0,
            "totalCollisions": 0,
        }

        self.initialize_agents(num_agents)

    def initialize_agents(self, num_agents: int) -> None:
        """Create N agents with random positions and velocities."""
        start = self.agent_count
        end = self.agent_count + num_agents
        for i in range(start, end):
            self.agents[i] = Agent.create_random(
                agent_id=i,
                bounds=self.bounds,
                max_speed=self.max_speed,
                trust_quota=self.trust_quota,
            )
        self.agent_count = len(self.agents)

    def update_metrics(self) -> None:
        """Calculate aggregate metrics for broadcasting."""
        n = len(self.agents)
        if n == 0:
            self.metrics["avgTrust"] = 0.0
            self.metrics["giniCoefficient"] = 0.0
            self.metrics["tradeSuccessRate"] = 0.0
            return

        trusts = [a.trust for a in self.agents.values()]
        avg_trust = sum(trusts) / n
        self.metrics["avgTrust"] = avg_trust

        # Gini coefficient for trust distribution
        # (safe for small n; O(n log n))
        sorted_trusts = sorted(trusts)
        cum = 0.0
        for i, v in enumerate(sorted_trusts, start=1):
            cum += i * v
        total = sum(sorted_trusts)
        if total <= 1e-12:
            gini = 0.0
        else:
            gini = (2.0 * cum) / (n * total) - (n + 1) / n
        self.metrics["giniCoefficient"] = max(0.0, min(1.0, gini))

        tc = self.metrics.get("tradeCount", 0)
        cc = self.metrics.get("totalCollisions", 0)
        self.metrics["tradeSuccessRate"] = (tc / cc) if cc > 0 else 0.0

    def add_event(self, event_type: str, data: dict) -> None:
        """Log interesting events for frontend alerts."""
        self.events.append({"tick": self.tick, "type": event_type, "data": data})
        # keep events bounded
        if len(self.events) > 5000:
            self.events = self.events[-2500:]

    def to_dict(self) -> dict:
        """Export full state (debug / REST)."""
        return {
            "tick": self.tick,
            "config": {
                "trustDecay": self.trust_decay,
                "trustQuota": self.trust_quota,
                "bounds": self.bounds,
                "maxSpeed": self.max_speed,
                "globalAlpha": self.global_alpha,
                "globalBeta": self.global_beta,
            },
            "agents": [a.to_dict() for a in self.agents.values()],
            "metrics": dict(self.metrics),
            "events": list(self.events[-200:]),
            "collisionLog": list(self.collision_log[-200:]),
        }
    
    def to_broadcast_dict(self) -> dict:
        """Optimized state for WebSocket broadcast (your required format)."""
        return {
            "type": "state_update",
            "payload": {
                "tick": self.tick,
                "agents": [a.to_minimal_dict() for a in self.agents.values()],
                "metrics": dict(self.metrics),
                "bounds": self.bounds,
            },
        }
