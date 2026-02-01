# backend/services/simulation.py
from models.state import SimulationState, MAX_GROUPS
from services.collision import CollisionDetector
from services.collision_response import (
    apply_soft_separation,
    apply_neutral_bounce,
    apply_hard_bounce,
)
from typing import Optional, Callable


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

    def _ensure_state(self, trust_decay: float = 0.05, trust_quota: float = 0.3):
        """Create empty state container if it doesn't exist yet."""
        if not self.state:
            self.state = SimulationState(
                num_agents=0,
                trust_decay=float(trust_decay),
                trust_quota=float(trust_quota),
            )
        if not self.collision_detector:
            self.collision_detector = CollisionDetector(
                collision_radius=self.collision_radius
            )

    def _get_group_params(self, agent):
        """Get alpha/beta for an agent from their group."""
        group = self.state.groups.get(agent.group_id)
        if group:
            return group.global_alpha, group.global_beta
        return 0.10, 0.05

    def _clamp(self, v: float) -> float:
        return max(0.0, min(1.0, v))

    def _resolve_collision_trust(self, a, b) -> bool:
        """Resolve trust for a collision pair ONCE.

        Checks both skill directions.
        Each agent's trust changes use their OWN group's alpha/beta.
        Returns True if a trade occurred.
        """
        # Check skill match in both directions
        ab_match = (a.skill_possessed == b.skill_needed)  # a can sell to b
        ba_match = (b.skill_possessed == a.skill_needed)  # b can sell to a

        if not ab_match and not ba_match:
            # No skill match at all — no trust change
            return False

        a_alpha, a_beta = self._get_group_params(a)
        b_alpha, b_beta = self._get_group_params(b)

        # Use per-agent overrides if set (custom agents)
        a_alpha = getattr(a, "trust_alpha", a_alpha)
        a_beta = getattr(a, "trust_beta", a_beta)
        b_alpha = getattr(b, "trust_alpha", b_alpha)
        b_beta = getattr(b, "trust_beta", b_beta)

        a_ok = (a.trust >= a.trust_quota)
        b_ok = (b.trust >= b.trust_quota)

        # CASE 1: Neither meets quota → no change
        if not a_ok and not b_ok:
            return False

        # CASE 2: Both meet quota AND skills match → trade, both trust UP
        if a_ok and b_ok:
            a.trust = self._clamp(a.trust + a_alpha)
            b.trust = self._clamp(b.trust + b_alpha)
            return True

        # CASE 3: One meets, other doesn't → the one who met loses trust
        if a_ok and not b_ok:
            a.trust = self._clamp(a.trust - a_beta)
            return False

        if b_ok and not a_ok:
            b.trust = self._clamp(b.trust - b_beta)
            return False

        return False

    def start(self, num_agents: int, trust_decay: float, trust_quota: float):
        """Start the simulation.

        If groups were pre-configured, keeps them and just starts the loop.
        If no state, creates Group 0 with num_agents.
        If state exists but zero agents anywhere, populates Group 0.
        """
        if self.state and self.state.tick > 0:
            self.running = True
            return

        if not self.state:
            self.state = SimulationState(
                num_agents=int(num_agents),
                trust_decay=float(trust_decay),
                trust_quota=float(trust_quota),
            )
        else:
            self.state.trust_decay = float(trust_decay)
            self.state.trust_quota = float(trust_quota)

            total_agents = sum(g.agent_count for g in self.state.groups.values())
            if total_agents == 0:
                if 0 in self.state.groups:
                    group = self.state.groups[0]
                    group.trust_decay = float(trust_decay)
                    group.trust_quota = float(trust_quota)
                    from models.agent import Agent
                    for _ in range(int(num_agents)):
                        agent = Agent.create_random(
                            agent_id=self.state.allocate_agent_id(),
                            bounds=self.state.bounds,
                            max_speed=self.state.max_speed,
                            trust_quota=float(trust_quota),
                        )
                        agent.group_id = 0
                        group.add_agent(agent)
                else:
                    self.state._init_group(0, int(num_agents))

        if not self.collision_detector:
            self.collision_detector = CollisionDetector(
                collision_radius=self.collision_radius
            )

        self.running = True
        self.tick_counter = 0

    def step(self):
        """Single simulation tick — ALL agents in one shared physics space."""
        if not self.running or not self.state:
            return

        self.tick_counter += 1
        self.state.tick += 1

        # Flat dict of ALL agents across all groups
        all_agents = self.state.all_agents
        bounds = self.state.bounds

        if not all_agents:
            return

        # ---- 1) Single collision pass across ALL agents ----
        try:
            pairs = self.collision_detector.detect_collisions(all_agents)
        except Exception:
            pairs = []

        self.state.global_metrics["totalCollisions"] += len(pairs)
        trade_directions = 0

        # ---- 2) Resolve collisions ----
        for id_a, id_b in pairs:
            a = all_agents[id_a]
            b = all_agents[id_b]

            # Resolve trust ONCE per pair.
            # Each agent's trust change uses their OWN group's alpha/beta.
            trade = self._resolve_collision_trust(a, b)

            if trade:
                trade_directions += 1
                a.trade_count += 1
                b.trade_count += 1
                a.last_trade_tick = self.state.tick
                b.last_trade_tick = self.state.tick

            # Physics — same for everyone
            radius = self.collision_detector.collision_radius
            if trade:
                apply_soft_separation(a, b, radius)
            else:
                # Check if skills matched at all (at least one direction)
                skills_ab = (a.skill_possessed == b.skill_needed)
                skills_ba = (b.skill_possessed == a.skill_needed)
                if skills_ab or skills_ba:
                    apply_hard_bounce(a, b, radius)
                else:
                    apply_neutral_bounce(a, b, radius)

            self.state.collision_log_global.append({
                "tick": self.state.tick,
                "pair": (a.agent_id, b.agent_id),
                "trade": trade,
            })

        # Cap collision log
        if len(self.state.collision_log_global) > 5000:
            self.state.collision_log_global = self.state.collision_log_global[-2500:]

        # ---- 3) Motion — per-agent speed from their group ----
        for agent in all_agents.values():
            group = self.state.groups.get(agent.group_id)
            speed_mult = group.speed_multiplier if group else 1.0
            agent.update_position(self.dt * speed_mult, bounds)
            MAX_SPEED = getattr(agent, "max_speed", 80.0)
            agent.vx = max(min(agent.vx, MAX_SPEED), -MAX_SPEED)
            agent.vy = max(min(agent.vy, MAX_SPEED), -MAX_SPEED)

        # ---- 4) Global trade metrics ----
        self.state.global_metrics["tradeCount"] += trade_directions
        cc = self.state.global_metrics["totalCollisions"]
        tc = self.state.global_metrics["tradeCount"]
        self.state.global_metrics["tradeSuccessRate"] = (tc / cc) if cc > 0 else 0.0

        # ---- 5) Trust decay — per-group rate applied to that group's agents ----
        if self.decay_interval_ticks > 0 and self.tick_counter % self.decay_interval_ticks == 0:
            for group in self.state.groups.values():
                decay = max(0.0, min(1.0, group.trust_decay))
                factor = 1.0 - decay
                for agent in group.agents.values():
                    agent.apply_decay(factor)

        # ---- 6) Update metrics (global + per-group) ----
        self.state.update_metrics()

    def create_group(self, group_id: int, num_agents: int = 0, config: dict = None) -> dict:
        self._ensure_state()
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
            return {"error": "No simulation state"}
        try:
            self.state.switch_group(group_id)
            return {"status": "ok", "activeGroupId": group_id}
        except ValueError as e:
            return {"error": str(e)}

    def update_group_config(self, group_id: int, params: dict) -> dict:
        if not self.state:
            return {"error": "No simulation state"}
        if group_id not in self.state.groups:
            return {"error": f"Group {group_id} does not exist"}
        group = self.state.groups[group_id]
        group.update_config(params)
        print(f"Updated Group {group_id} config: {params}")
        return {"status": "ok", "groupId": group_id, "config": group.get_config()}

    def add_custom_agent(self, params: dict):
        self._ensure_state()

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
        if not params:
            return
        if "dt" in params:
            self.dt = float(params["dt"])
        if "broadcast_interval" in params:
            self.broadcast_interval = max(1, int(params["broadcast_interval"]))
        if "collision_radius" in params:
            self.collision_radius = float(params["collision_radius"])
        if self.state:
            group_params = {}
            if "trust_decay" in params:
                group_params["trustDecay"] = params["trust_decay"]
            if "trust_quota" in params:
                group_params["trustQuota"] = params["trust_quota"]
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