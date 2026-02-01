# backend/models/state.py
from __future__ import annotations
from typing import Dict, List, Tuple

from .agent import Agent

MAX_GROUPS = 5


class AgentGroup:
    """Independent group with own agents, config, and metrics."""

    def __init__(
        self,
        group_id: int,
        bounds: Tuple[float, float],
        trust_quota: float = 0.5,
        trust_decay: float = 0.05,
        global_alpha: float = 0.10,
        global_beta: float = 0.05,
        speed_multiplier: float = 1.0,
    ):
        self.group_id: int = group_id
        self.agents: Dict[int, Agent] = {}
        self.bounds: Tuple[float, float] = bounds

        # Per-group config
        self.trust_quota: float = trust_quota
        self.trust_decay: float = trust_decay
        self.global_alpha: float = global_alpha
        self.global_beta: float = global_beta
        self.speed_multiplier: float = speed_multiplier

        self.collision_log: List[dict] = []
        self.metrics: dict = {
            "avgTrust": 0.0,
            "giniCoefficient": 0.0,
            "tradeSuccessRate": 0.0,
            "tradeCount": 0,
            "totalCollisions": 0,
        }

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    def add_agent(self, agent: Agent) -> None:
        agent.group_id = self.group_id
        self.agents[agent.agent_id] = agent

    def update_metrics(self) -> None:
        n = len(self.agents)
        if n == 0:
            self.metrics["avgTrust"] = 0.0
            self.metrics["giniCoefficient"] = 0.0
            self.metrics["tradeSuccessRate"] = 0.0
            return

        trusts = [a.trust for a in self.agents.values()]
        avg_trust = sum(trusts) / n
        self.metrics["avgTrust"] = avg_trust

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

    def get_config(self) -> dict:
        return {
            "trustQuota": self.trust_quota,
            "trustDecay": self.trust_decay,
            "globalAlpha": self.global_alpha,
            "globalBeta": self.global_beta,
            "speedMultiplier": self.speed_multiplier,
        }

    def update_config(self, params: dict) -> None:
        if "trustDecay" in params:
            self.trust_decay = float(params["trustDecay"])
        if "trustQuota" in params:
            self.trust_quota = float(params["trustQuota"])
            for a in self.agents.values():
                a.trust_quota = self.trust_quota
        if "globalAlpha" in params:
            self.global_alpha = float(params["globalAlpha"])
        if "globalBeta" in params:
            self.global_beta = float(params["globalBeta"])
        if "speedMultiplier" in params:
            self.speed_multiplier = float(params["speedMultiplier"])

    def to_broadcast_dict(self) -> dict:
        return {
            "groupId": self.group_id,
            "agents": [a.to_minimal_dict() for a in self.agents.values()],
            "metrics": dict(self.metrics),
            "config": self.get_config(),
            "agentCount": self.agent_count,
        }


class SimulationState:
    def __init__(
        self,
        num_agents: int,
        trust_decay: float,
        trust_quota: float,
        bounds: Tuple[float, float] = (1000.0, 1000.0),
        max_speed: float = 50.0,
    ):
        self.tick: int = 0
        self.trust_decay: float = float(trust_decay)
        self.trust_quota: float = float(trust_quota)
        self.bounds: Tuple[float, float] = bounds
        self.max_speed: float = max_speed
        self.global_alpha: float = 0.10
        self.global_beta: float = 0.05

        self.groups: Dict[int, AgentGroup] = {}
        self.active_group_id: int = 0
        self._next_agent_id: int = 0
        self.events: List[dict] = []

        self._init_group(0, num_agents)

    # ---- Backward compat ----

    @property
    def agents(self) -> Dict[int, Agent]:
        return self.active_group.agents

    @property
    def active_group(self) -> AgentGroup:
        return self.groups[self.active_group_id]

    @property
    def agent_count(self) -> int:
        return sum(g.agent_count for g in self.groups.values())

    @agent_count.setter
    def agent_count(self, value: int):
        pass

    @property
    def metrics(self) -> dict:
        return self.active_group.metrics

    @metrics.setter
    def metrics(self, value: dict):
        pass

    @property
    def collision_log(self) -> List[dict]:
        return self.active_group.collision_log

    @collision_log.setter
    def collision_log(self, value: List[dict]):
        pass

    # ---- Group management ----

    def _init_group(self, group_id: int, num_agents: int, **cfg) -> AgentGroup:
        group = AgentGroup(
            group_id=group_id,
            bounds=self.bounds,
            trust_quota=cfg.get("trust_quota", self.trust_quota),
            trust_decay=cfg.get("trust_decay", self.trust_decay),
            global_alpha=cfg.get("global_alpha", self.global_alpha),
            global_beta=cfg.get("global_beta", self.global_beta),
            speed_multiplier=cfg.get("speed_multiplier", 1.0),
        )
        for _ in range(num_agents):
            agent = Agent.create_random(
                agent_id=self._next_agent_id,
                bounds=self.bounds,
                max_speed=self.max_speed,
                trust_quota=group.trust_quota,
            )
            agent.group_id = group_id
            group.agents[agent.agent_id] = agent
            self._next_agent_id += 1
        self.groups[group_id] = group
        return group

    def get_or_create_group(self, group_id: int, num_agents: int = 0, config: dict = None) -> AgentGroup:
        if group_id in self.groups:
            return self.groups[group_id]
        if len(self.groups) >= MAX_GROUPS:
            raise ValueError(f"Maximum of {MAX_GROUPS} groups reached")
        if group_id < 0 or group_id >= MAX_GROUPS:
            raise ValueError(f"Group ID must be 0..{MAX_GROUPS - 1}")
        cfg = config or {}
        return self._init_group(
            group_id, num_agents,
            trust_quota=cfg.get("trustQuota", self.trust_quota),
            trust_decay=cfg.get("trustDecay", self.trust_decay),
            global_alpha=cfg.get("globalAlpha", self.global_alpha),
            global_beta=cfg.get("globalBeta", self.global_beta),
            speed_multiplier=cfg.get("speedMultiplier", 1.0),
        )

    def switch_group(self, group_id: int) -> None:
        if group_id not in self.groups:
            raise ValueError(f"Group {group_id} does not exist")
        self.active_group_id = group_id

    def allocate_agent_id(self) -> int:
        aid = self._next_agent_id
        self._next_agent_id += 1
        return aid

    def update_metrics(self) -> None:
        for group in self.groups.values():
            group.update_metrics()

    def add_event(self, event_type: str, data: dict) -> None:
        self.events.append({"tick": self.tick, "type": event_type, "data": data})
        if len(self.events) > 5000:
            self.events = self.events[-2500:]

    def to_dict(self) -> dict:
        all_agents = []
        for g in self.groups.values():
            all_agents.extend(a.to_dict() for a in g.agents.values())
        return {
            "tick": self.tick,
            "activeGroupId": self.active_group_id,
            "groups": {gid: g.to_broadcast_dict() for gid, g in self.groups.items()},
            "agents": all_agents,
            "metrics": dict(self.active_group.metrics),
            "events": list(self.events[-200:]),
        }

    def to_broadcast_dict(self) -> dict:
        # ALL agents from ALL groups — they share one canvas
        all_agents = []
        for g in self.groups.values():
            all_agents.extend(a.to_minimal_dict() for a in g.agents.values())

        return {
            "type": "state_update",
            "payload": {
                "tick": self.tick,
                "activeGroupId": self.active_group_id,
                "groups": {
                    str(gid): g.to_broadcast_dict()
                    for gid, g in self.groups.items()
                },
                "agents": all_agents,
                "metrics": dict(self.active_group.metrics),
                "bounds": self.bounds,
            },
        }