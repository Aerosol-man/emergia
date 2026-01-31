# backend/models/agent.py
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Agent:
    agent_id: int
    x: float
    y: float
    vx: float
    vy: float
    skill_possessed: str
    skill_needed: str
    trust: float
    trust_quota: float
    trust_alpha: Optional[float] = None
    trust_beta: Optional[float] = None
    
    def update_position(self, dt: float, bounds: tuple[float, float]):
        """Update agent position and handle wall bounces"""
        pass
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary for JSON serialization"""
        return asdict(self)
    
    def to_minimal_dict(self) -> dict:
        """Minimal payload for WebSocket updates"""
        return {
            "id": self.agent_id,
            "x": self.x,
            "y": self.y,
            "trust": self.trust,
            "skillPossessed": self.skill_possessed,
            "skillNeeded": self.skill_needed
        }