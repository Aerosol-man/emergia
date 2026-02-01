# backend/models/state.py
from __future__ import annotations
from typing import Dict, List, Tuple, Any
from .agent import Agent
import math

MAX_GROUPS = 5

def _safe_median(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return float((s[mid - 1] + s[mid]) / 2.0)

def _trust_stats(values: List[float]) -> dict:
    if not values:
        return {"avg": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    return {
        "avg": float(sum(values) / len(values)),
        "median": float(_safe_median(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }

def _series_stats(values: List[float]) -> dict:
    # same as trust stats, but semantically “over time series”
    return _trust_stats(values)


class AgentGroup:
    """Config label for a subset of agents. Not a physics boundary."""

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

        # Per-group metrics (for comparison/reports)
        self.metrics: dict = {
            "avgTrust": 0.0,
            "giniCoefficient": 0.0,
            "agentCount": 0,
        }

        # Per-group counters (accumulated over whole sim)
        self.counters: dict = {
            "totalCollisions": 0,
            "tradeCount": 0,
        }

    @property
    def agent_count(self) -> int:
        return len(self.agents)

    def add_agent(self, agent: Agent) -> None:
        agent.group_id = self.group_id
        self.agents[agent.agent_id] = agent

    def update_metrics(self) -> None:
        n = len(self.agents)
        self.metrics["agentCount"] = n
        if n == 0:
            self.metrics["avgTrust"] = 0.0
            self.metrics["giniCoefficient"] = 0.0
            return

        trusts = [a.trust for a in self.agents.values()]
        self.metrics["avgTrust"] = sum(trusts) / n

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

        # Global collision log
        self.collision_log_global: List[dict] = []

        # Global metrics across ALL agents
        self.global_metrics: dict = {
            "avgTrust": 0.0,
            "giniCoefficient": 0.0,
            "tradeSuccessRate": 0.0,
            "tradeCount": 0,
            "totalCollisions": 0,
        }

        # reporting
        self.reports: List[dict] = []
        self.report_interval_ticks: int = 60  # generate snapshot every 60 ticks by default

        if num_agents > 0:
            self._init_group(0, num_agents)

    # ---- All agents flat view ----

    @property
    def all_agents(self) -> Dict[int, Agent]:
        """Single flat dict of every agent across all groups."""
        merged = {}
        for group in self.groups.values():
            merged.update(group.agents)
        return merged

    # ---- Backward compat ----

    @property
    def agents(self) -> Dict[int, Agent]:
        """For backward compat with collision detector etc."""
        return self.all_agents

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
        return self.global_metrics

    @metrics.setter
    def metrics(self, value: dict):
        pass

    @property
    def collision_log(self) -> List[dict]:
        return self.collision_log_global

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

    # ---- Metrics ----

    def update_metrics(self) -> None:
        """Compute global metrics across ALL agents, plus per-group."""
        # Per-group
        for group in self.groups.values():
            group.update_metrics()

        # Global
        all_agents_list = list(self.all_agents.values())
        n = len(all_agents_list)
        if n == 0:
            self.global_metrics["avgTrust"] = 0.0
            self.global_metrics["giniCoefficient"] = 0.0
            return

        trusts = [a.trust for a in all_agents_list]
        self.global_metrics["avgTrust"] = sum(trusts) / n

        sorted_trusts = sorted(trusts)
        cum = 0.0
        for i, v in enumerate(sorted_trusts, start=1):
            cum += i * v
        total = sum(sorted_trusts)
        if total <= 1e-12:
            gini = 0.0
        else:
            gini = (2.0 * cum) / (n * total) - (n + 1) / n
        self.global_metrics["giniCoefficient"] = max(0.0, min(1.0, gini))

        tc = self.global_metrics.get("tradeCount", 0)
        cc = self.global_metrics.get("totalCollisions", 0)
        self.global_metrics["tradeSuccessRate"] = (tc / cc) if cc > 0 else 0.0

    # ---- Events ----

    def add_event(self, event_type: str, data: dict) -> None:
        self.events.append({"tick": self.tick, "type": event_type, "data": data})
        if len(self.events) > 5000:
            self.events = self.events[-2500:]

    # ---- Serialization ----

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "activeGroupId": self.active_group_id,
            "groups": {gid: g.to_broadcast_dict() for gid, g in self.groups.items()},
            "agents": [a.to_dict() for a in self.all_agents.values()],
            "metrics": dict(self.global_metrics),
            "events": list(self.events[-200:]),
        }

    def to_broadcast_dict(self) -> dict:
        return {
            "type": "state_update",
            "payload": {
                "tick": self.tick,
                "activeGroupId": self.active_group_id,
                "groups": {
                    str(gid): g.to_broadcast_dict()
                    for gid, g in self.groups.items()
                },
                "agents": [a.to_minimal_dict() for a in self.all_agents.values()],
                "metrics": dict(self.global_metrics),
                "bounds": self.bounds,
            },
        }
    

    def record_report_snapshot(self) -> None:
        """
        Capture a rolling snapshot every report interval.
        Stores per-group + global metrics at this tick.
        """
        print("Compiling snapshot report...")
        # ensure metrics are fresh
        self.update_metrics()

        group_payload = {}
        for gid, g in self.groups.items():
            group_payload[str(gid)] = {
                "tick": self.tick,
                "groupId": gid,
                "agentCount": g.agent_count,
                "avgTrust": float(g.metrics.get("avgTrust", 0.0)),
                "giniCoefficient": float(g.metrics.get("giniCoefficient", 0.0)),
                "totalCollisions": int(g.counters.get("totalCollisions", 0)),
                "tradeCount": int(g.counters.get("tradeCount", 0)),
            }

        print("group payload made")

        snap = {
            "tick": self.tick,
            "global": {
                "avgTrust": float(self.global_metrics.get("avgTrust", 0.0)),
                "giniCoefficient": float(self.global_metrics.get("giniCoefficient", 0.0)),
                "totalCollisions": int(self.global_metrics.get("totalCollisions", 0)),
                "tradeCount": int(self.global_metrics.get("tradeCount", 0)),
                "tradeSuccessRate": float(self.global_metrics.get("tradeSuccessRate", 0.0)),
                "agentCount": int(self.agent_count),
            },
            "groups": group_payload,
        }  

        print("aobut to add to reports list")

        self.reports.append(snap)

        print(f"=> added to report list! {snap}")
        
        # cap to avoid memory blowups (tune as needed)
        if len(self.reports) > 2000:
            self.reports = self.reports[-1000:]


    def compile_final_report(self) -> dict:
        """
        Final aggregated report:
        - Trust stats: computed from final trust values (global + per group)
        - Gini stats: computed from rolling report series (global + per group)
        - Collisions/trades totals: from counters
        """
        all_agents = list(self.all_agents.values())
        global_trusts = [a.trust for a in all_agents]

        # --- Global trust stats (final distribution) ---
        global_trust_stats = _trust_stats(global_trusts)

        # --- Global gini stats (over time) ---
        global_gini_series = []
        for r in self.reports:
            g = r.get("global", {}).get("giniCoefficient")
            if isinstance(g, (int, float)):
                global_gini_series.append(float(g))
        global_gini_stats = _series_stats(global_gini_series)

        # --- Global collisions/trades ---
        total_collisions = int(self.global_metrics.get("totalCollisions", 0))
        trade_count = int(self.global_metrics.get("tradeCount", 0))
        trade_success = (trade_count / total_collisions) if total_collisions > 0 else 0.0

        # --- Per-group ---
        group_reports = {}
        for gid, group in self.groups.items():
            trusts = [a.trust for a in group.agents.values()]
            trust_stats = _trust_stats(trusts)

            gini_series = []
            for r in self.reports:
                gg = r.get("groups", {}).get(str(gid), {}).get("giniCoefficient")
                if isinstance(gg, (int, float)):
                    gini_series.append(float(gg))
            gini_stats = _series_stats(gini_series)

            gc = int(group.counters.get("totalCollisions", 0))
            gt = int(group.counters.get("tradeCount", 0))
            gsuccess = (gt / gc) if gc > 0 else 0.0

            group_reports[str(gid)] = {
                "groupId": gid,
                "agentCount": group.agent_count,
                "trust": trust_stats,
                "giniCoefficient": gini_stats,
                "totalCollisions": gc,
                "tradeCount": gt,
                "tradeSuccessRate": float(gsuccess),
                "config": group.get_config(),
            }

        return {
            "tickEnd": self.tick,
            "global": {
                "agentCount": self.agent_count,
                "trust": global_trust_stats,
                "giniCoefficient": global_gini_stats,
                "totalCollisions": total_collisions,
                "tradeCount": trade_count,
                "tradeSuccessRate": float(trade_success),
            },
            "groups": group_reports,
            # Optional: return some rolling snapshots for frontend charts
            "rolling": {
                "intervalTicks": int(self.report_interval_ticks),
                "count": len(self.reports),
                "snapshots": self.reports[-200:],  # last N only
            },
        }
