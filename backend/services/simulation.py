from models.state import SimulationState
from services.collision import CollisionDetector
from services.trust import TrustEngine
from typing import Optional, Callable
import asyncio


class SimulationEngine:
    def __init__(self):
        self.state: SimulationState = None
        self.collision_detector: CollisionDetector = None
        self.trust_engine: TrustEngine = None
        self.running: bool = False

        # time step (seconds)
        self.dt: float = 0.016  # ~60 FPS

        # broadcasting
        self.broadcast_callback: Optional[Callable] = None
        self.tick_counter: int = 0
        self.broadcast_interval: int = 1  # Broadcast every N ticks

        # simulation params (MVP defaults)
        self.collision_radius: float = 8.0
        self.decay_interval_ticks: int = 30  # apply decay every X ticks

    def set_broadcast_callback(self, callback: Callable):
        """Set callback for broadcasting state updates"""
        self.broadcast_callback = callback

    def start(self, num_agents: int, trust_decay: float, trust_quota: float):
        """Initialize and start simulation (MVP)."""
        self.state = SimulationState(
            num_agents=int(num_agents),
            trust_decay=float(trust_decay),
            trust_quota=float(trust_quota),
        )

        if hasattr(self.state, "initialize_agents"):
            try:
                if getattr(self.state, "agent_count", 0) == 0:
                    self.state.initialize_agents(int(num_agents))
            except TypeError:
                pass

        self.collision_detector = CollisionDetector()

        alpha = getattr(self.state, "global_alpha", 0.10)
        beta = getattr(self.state, "global_beta", 0.05)
        self.trust_engine = TrustEngine(global_alpha=alpha, global_beta=beta)

        self.running = True
        self.tick_counter = 0

        if hasattr(self.state, "metrics") and isinstance(self.state.metrics, dict):
            self.state.metrics.setdefault("avgTrust", 0.0)
            self.state.metrics.setdefault("tradeCount", 0)
            self.state.metrics.setdefault("totalCollisions", 0)
            self.state.metrics.setdefault("tradeSuccessRate", 0.0)

    def step(self):
        """Single simulation tick."""
        if not self.running or not self.state:
            return

        self.tick_counter += 1

        if hasattr(self.state, "tick"):
            self.state.tick += 1

        # ---- 1) Update motion ----
        bounds = getattr(self.state, "bounds", (1000.0, 1000.0))
        agents_dict = getattr(self.state, "agents", {})
        agents_list = list(agents_dict.values())

        for agent in agents_list:
            agent.update_position(self.dt, bounds)

        # ---- 2) Collisions ----
        pairs = []
        if self.collision_detector:
            if hasattr(self.collision_detector, "detect_collisions"):
                try:
                    pairs = self.collision_detector.detect_collisions(agents_dict)
                except TypeError:
                    pairs = []

        total_collisions = len(pairs)
        trade_directions_this_tick = 0

        if hasattr(self.state, "metrics") and isinstance(self.state.metrics, dict):
            self.state.metrics["totalCollisions"] = self.state.metrics.get("totalCollisions", 0) + total_collisions

        # ---- 3) Trust logic per collision (directional) ----
        # detect_collisions returns (agent_id, agent_id) tuples,
        # so we must resolve them to actual Agent objects
        for id_a, id_b in pairs:
            a = agents_dict[id_a]
            b = agents_dict[id_b]

            # OnCollide(a seller, b buyer)
            info_ab = self.trust_engine.apply_collision_logic(a, b)
            # OnCollide(b seller, a buyer)
            info_ba = self.trust_engine.apply_collision_logic(b, a)

            # count trades (directional)
            trade_directions_this_tick += int(bool(info_ab.get("trade", False)))
            trade_directions_this_tick += int(bool(info_ba.get("trade", False)))

            if info_ab.get("trade", False):
                if hasattr(a, "trade_count"):
                    a.trade_count += 1
                if hasattr(b, "trade_count"):
                    b.trade_count += 1
                if hasattr(a, "last_trade_tick"):
                    a.last_trade_tick = getattr(self.state, "tick", self.tick_counter)
                if hasattr(b, "last_trade_tick"):
                    b.last_trade_tick = getattr(self.state, "tick", self.tick_counter)

            if info_ba.get("trade", False):
                if hasattr(a, "trade_count"):
                    a.trade_count += 1
                if hasattr(b, "trade_count"):
                    b.trade_count += 1
                if hasattr(a, "last_trade_tick"):
                    a.last_trade_tick = getattr(self.state, "tick", self.tick_counter)
                if hasattr(b, "last_trade_tick"):
                    b.last_trade_tick = getattr(self.state, "tick", self.tick_counter)

            if hasattr(self.state, "collision_log") and isinstance(self.state.collision_log, list):
                self.state.collision_log.append({
                    "tick": getattr(self.state, "tick", self.tick_counter),
                    "pair": (a.agent_id, b.agent_id),
                    "ab": info_ab,
                    "ba": info_ba,
                })

        if hasattr(self.state, "metrics") and isinstance(self.state.metrics, dict):
            self.state.metrics["tradeCount"] = self.state.metrics.get("tradeCount", 0) + trade_directions_this_tick
            cc = self.state.metrics.get("totalCollisions", 0)
            tc = self.state.metrics.get("tradeCount", 0)
            self.state.metrics["tradeSuccessRate"] = (tc / cc) if cc > 0 else 0.0

        # ---- 4) Trust decay (every X ticks) ----
        if self.decay_interval_ticks > 0 and (self.tick_counter % self.decay_interval_ticks == 0):
            trust_decay = float(getattr(self.state, "trust_decay", 0.0))
            decay_factor = 1.0 - trust_decay
            decay_factor = max(0.0, min(1.0, decay_factor))
            self.trust_engine.apply_decay(agents_dict, decay_factor)

        # ---- 5) Update metrics ----
        if hasattr(self.state, "update_metrics"):
            self.state.update_metrics()
        else:
            if hasattr(self.state, "metrics") and isinstance(self.state.metrics, dict) and len(agents_list) > 0:
                avg_trust = sum(getattr(a, "trust", 0.0) for a in agents_list) / len(agents_list)
                self.state.metrics["avgTrust"] = avg_trust

    def should_broadcast(self) -> bool:
        """Check if this tick should trigger a broadcast"""
        return self.tick_counter % self.broadcast_interval == 0

    def update_parameters(self, params: dict):
        """Update simulation parameters on-the-fly."""
        if not params:
            return

        if "dt" in params:
            self.dt = float(params["dt"])
        if "broadcast_interval" in params:
            self.broadcast_interval = max(1, int(params["broadcast_interval"]))
        if "collision_radius" in params:
            self.collision_radius = float(params["collision_radius"])
        if "decay_interval_ticks" in params:
            self.decay_interval_ticks = max(1, int(params["decay_interval_ticks"]))

        if self.state:
            if "trust_decay" in params:
                self.state.trust_decay = float(params["trust_decay"])
            if "trust_quota" in params:
                self.state.trust_quota = float(params["trust_quota"])
                if hasattr(self.state, "agents"):
                    for a in self.state.agents.values():
                        a.trust_quota = self.state.trust_quota

        if self.trust_engine:
            if "global_alpha" in params:
                self.trust_engine.global_alpha = float(params["global_alpha"])
            if "global_beta" in params:
                self.trust_engine.global_beta = float(params["global_beta"])

    def pause(self):
        """Pause simulation"""
        self.running = False

    def reset(self):
        """Reset simulation state"""
        self.running = False
        self.state = None
        self.collision_detector = None
        self.trust_engine = None
        self.tick_counter = 0

    def get_state(self) -> dict:
        """Return current state as dict"""
        if not self.state:
            return {}
        if hasattr(self.state, "to_dict"):
            return self.state.to_dict()
        return {
            "tick": getattr(self.state, "tick", self.tick_counter),
            "agents": [a.to_dict() for a in getattr(self.state, "agents", {}).values()],
            "metrics": getattr(self.state, "metrics", {}),
        }

    def get_broadcast_state(self) -> dict:
        """Return optimized state for WebSocket"""
        if self.state:
            return self.state.to_broadcast_dict()
        return {}