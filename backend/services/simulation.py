# backend/services/simulation.py
from models.state import SimulationState, MAX_GROUPS
from services.collision import CollisionDetector
from services.trust import TrustEngine
from services.collision_response import (
    apply_soft_separation,
    apply_neutral_bounce,
    apply_hard_bounce,
)
from typing import Optional, Callable
import asyncio


class SimulationEngine:
    def __init__(self):
        self.state: SimulationState = None
        self.collision_detector: CollisionDetector = None
        self.running: bool = False

        self.dt: float = 0.016
        self.broadcast_callback: Optional[Callable] = None
        self.tick_counter: int = 0
        self.broadcast_interval: int = 1
        self.collision_radius: float = 8.0
        self.decay_interval_ticks: int = 30

    def set_broadcast_callback(self, callback: Callable):
        self.broadcast_callback = callback

    def start(self, num_agents: int, trust_decay: float, trust_quota: float):
        self.state = SimulationState(
            num_agents=int(num_agents),
            trust_decay=float(trust_decay),
            trust_quota=float(trust_quota),
        )
        self.collision_detector = CollisionDetector(collision_radius=self.collision_radius)
        self.running = True
        self.tick_counter = 0

    def _step_group(self, group):
        """Run one tick for a single group using its own config."""
        agents_dict = group.agents
        if not agents_dict:
            return

        bounds = self.state.bounds

        # Use this group's trust engine params
        trust_engine = TrustEngine(
            global_alpha=group.global_alpha,
            global_beta=group.global_beta,
        )

        # dt scaled by group's speed multiplier
        dt = self.dt * group.speed_multiplier

        # 1) Collisions
        try:
            pairs = self.collision_detector.detect_collisions(agents_dict)
        except Exception:
            pairs = []

        group.metrics["totalCollisions"] += len(pairs)
        trade_directions = 0

        # 2) Resolve
        for id_a, id_b in pairs:
            a = agents_dict[id_a]
            b = agents_dict[id_b]

            info_ab = trust_engine.apply_collision_logic(a, b)
            info_ba = trust_engine.apply_collision_logic(b, a)

            trade_ab = bool(info_ab.get("trade", False))
            trade_ba = bool(info_ba.get("trade", False))
            trade_directions += int(trade_ab) + int(trade_ba)

            radius = self.collision_detector.collision_radius
            if trade_ab and trade_ba:
                apply_soft_separation(a, b, radius)
            elif trade_ab ^ trade_ba:
                apply_hard_bounce(a, b, radius)
            else:
                apply_neutral_bounce(a, b, radius)

            if trade_ab or trade_ba:
                a.trade_count += 1
                b.trade_count += 1
                a.last_trade_tick = self.state.tick
                b.last_trade_tick = self.state.tick

            group.collision_log.append({
                "tick": self.state.tick,
                "pair": (a.agent_id, b.agent_id),
                "ab": info_ab,
                "ba": info_ba,
            })

        # 3) Motion
        for agent in agents_dict.values():
            agent.update_position(dt, bounds)
            MAX_SPEED = getattr(agent, "max_speed", 80.0)
            agent.vx = max(min(agent.vx, MAX_SPEED), -MAX_SPEED)
            agent.vy = max(min(agent.vy, MAX_SPEED), -MAX_SPEED)

        # 4) Trade metrics
        group.metrics["tradeCount"] += trade_directions
        cc = group.metrics["totalCollisions"]
        tc = group.metrics["tradeCount"]
        group.metrics["tradeSuccessRate"] = (tc / cc) if cc > 0 else 0.0

    def step(self):
        if not self.running or not self.state:
            return

        self.tick_counter += 1
        self.state.tick += 1

        # Step ALL groups independently
        for group in self.state.groups.values():
            self._step_group(group)

        # Trust decay per group using that group's own decay rate
        if self.decay_interval_ticks > 0 and self.tick_counter % self.decay_interval_ticks == 0:
            for group in self.state.groups.values():
                decay = max(0.0, min(1.0, group.trust_decay))
                trust_engine = TrustEngine(
                    global_alpha=group.global_alpha,
                    global_beta=group.global_beta,
                )
                trust_engine.apply_decay(group.agents, 1.0 - decay)

        self.state.update_metrics()

    def create_group(self, group_id: int, num_agents: int = 0, config: dict = None) -> dict:
        if not self.state:
            return {"error": "Simulation not running"}
        try:
            group = self.state.get_or_create_group(group_id, num_agents, config)
            return {
                "status": "ok",
                "groupId": group_id,
                "agentCount": group.agent_count,
                "config": group.get_config(),
            }
        except ValueError as e:
            return {"error": str(e)}

    def switch_group(self, group_id: int) -> dict:
        if not self.state:
            return {"error": "Simulation not running"}
        try:
            self.state.switch_group(group_id)
            return {"status": "ok", "activeGroupId": group_id}
        except ValueError as e:
            return {"error": str(e)}

    def update_group_config(self, group_id: int, params: dict) -> dict:
        """Update config for a specific group independently."""
        if not self.state:
            return {"error": "Simulation not running"}
        if group_id not in self.state.groups:
            return {"error": f"Group {group_id} does not exist"}
        group = self.state.groups[group_id]
        group.update_config(params)
        print(f"Updated Group {group_id} config: {params}")
        return {"status": "ok", "groupId": group_id, "config": group.get_config()}

    def add_custom_agent(self, params: dict):
        if not self.state:
            return

        group_id = int(params.get("groupId", self.state.active_group_id))
        num_agents = int(params.get("numAgents", 1))
        quota = float(params.get("trustQuota", 0.5))
        alpha = float(params.get("trustGain", 0.1))
        beta = float(params.get("trustLoss", 0.05))

        group = self.state.get_or_create_group(group_id)

        from models.agent import Agent
        for _ in range(num_agents):
            new_id = self.state.allocate_agent_id()
            new_agent = Agent.create_random(
                agent_id=new_id,
                bounds=self.state.bounds,
                trust_quota=quota,
            )
            new_agent.trust_alpha = alpha
            new_agent.trust_beta = beta
            new_agent.is_custom = True
            new_agent.group_id = group_id
            group.add_agent(new_agent)

        print(f"Added {num_agents} agents to Group {group_id}: Q={quota}, A={alpha}, B={beta}")

    def should_broadcast(self) -> bool:
        return self.tick_counter % self.broadcast_interval == 0

    def update_parameters(self, params: dict):
        """Update global params (backward compat — affects active group)."""
        if not params:
            return
        if "dt" in params:
            self.dt = float(params["dt"])
        if "broadcast_interval" in params:
            self.broadcast_interval = max(1, int(params["broadcast_interval"]))
        if "collision_radius" in params:
            self.collision_radius = float(params["collision_radius"])
        if self.state:
            # Route to active group
            group_params = {}
            if "trust_decay" in params:
                group_params["trustDecay"] = params["trust_decay"]
            if "trust_quota" in params:
                group_params["trustQuota"] = params["trust_quota"]
            if "speedMultiplier" in params or "dt" in params:
                if "speedMultiplier" in params:
                    group_params["speedMultiplier"] = params["speedMultiplier"]
            if group_params:
                self.state.active_group.update_config(group_params)

    def pause(self):
        self.running = False

    def reset(self):
        self.running = False
        self.state = None
        self.collision_detector = None
        self.tick_counter = 0

    def get_state(self) -> dict:
        if not self.state:
            return {}
        return self.state.to_dict()

    def get_broadcast_state(self) -> dict:
        if self.state:
            return self.state.to_broadcast_dict()
        return {}