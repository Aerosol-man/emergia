# backend/models/state.py
from typing import Dict, List
from models.agent import Agent

class SimulationState:
    def __init__(self, num_agents: int, trust_decay: float, trust_quota: float):
        self.agents: Dict[int, Agent] = {}
        self.tick: int = 0
        self.trust_decay: float = trust_decay
        self.trust_quota: float = trust_quota
        self.collision_log: List[dict] = []
        self.global_alpha: float = 0.1
        self.global_beta: float = 0.05
        self.bounds: tuple[float, float] = (1000.0, 1000.0)
        self.metrics: dict = {
            "avg_trust": 0.0,
            "trade_count": 0,
            "total_collisions": 0
        }
        self.events: List[dict] = []
        
    def initialize_agents(self, num_agents: int):
        """Create N agents with random positions and velocities"""
        pass
    
    def update_metrics(self):
        """Calculate aggregate metrics for broadcasting"""
        pass
    
    def add_event(self, event_type: str, data: dict):
        """Log interesting events for frontend alerts"""
        pass
    
    def to_dict(self) -> dict:
        """Export full state as dictionary"""
        pass
    
    def to_broadcast_dict(self) -> dict:
        """Optimized state for WebSocket broadcast"""
        return {
            "type": "state_update",
            "tick": self.tick,
            "agents": [agent.to_minimal_dict() for agent in self.agents.values()],
            "metrics": self.metrics.copy()
        }