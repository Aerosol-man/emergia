# backend/models/agent.py
from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum, auto
import random
import math


class Skill(IntEnum):
    """
    Skills as IntEnum for fast integer comparison.
    IntEnum is faster than StrEnum since it compares integers directly.
    """
    COOKING = auto()
    CODING = auto()
    TEACHING = auto()
    BUILDING = auto()
    HEALING = auto()
    GROWING = auto()
    TRADING = auto()
    CRAFTING = auto()
    
    @classmethod
    def random(cls) -> 'Skill':
        """Return a random skill."""
        return random.choice(list(cls))
    
    @classmethod
    def random_pair(cls) -> tuple['Skill', 'Skill']:
        """Return two different random skills (possessed, needed)."""
        skills = list(cls)
        possessed = random.choice(skills)
        needed = random.choice([s for s in skills if s != possessed])
        return possessed, needed


@dataclass(slots=True)
class Agent:
    """
    Agent in the trust-based economy simulation.
    
    Uses __slots__ via dataclass(slots=True) for faster attribute access
    and reduced memory footprint.
    """
    agent_id: int
    x: float
    y: float
    vx: float
    vy: float
    skill_possessed: Skill
    skill_needed: Skill
    trust: float
    trust_quota: float
    trust_alpha: float = 1.0
    trust_beta: float = 1.0
    
    @classmethod
    def create_random(
        cls,
        agent_id: int,
        bounds: tuple[float, float],
        max_speed: float = 50.0,
        trust_quota: float = 0.5,
    ) -> 'Agent':
        """
        Factory method to create an agent with random position, velocity, and skills.
        
        Args:
            agent_id: Unique identifier for the agent
            bounds: (width, height) of the simulation space
            max_speed: Maximum initial speed in any direction
            trust_quota: Threshold for trust-based transactions
        """
        skill_possessed, skill_needed = Skill.random_pair()
        
        return cls(
            agent_id=agent_id,
            x=random.uniform(0, bounds[0]),
            y=random.uniform(0, bounds[1]),
            vx=random.uniform(-max_speed, max_speed),
            vy=random.uniform(-max_speed, max_speed),
            skill_possessed=skill_possessed,
            skill_needed=skill_needed,
            trust=random.uniform(0.3, 0.7),
            trust_quota=trust_quota,
        )
    
    def update_position(self, dt: float, bounds: tuple[float, float]) -> None:
        """
        Update agent position based on velocity and handle wall bounces.
        
        Args:
            dt: Time delta in seconds
            bounds: (width, height) of the simulation space
        """
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        width, height = bounds
        
        # Wall bounce - X axis
        if self.x <= 0:
            self.x = -self.x
            self.vx = -self.vx
        elif self.x >= width:
            self.x = 2 * width - self.x
            self.vx = -self.vx
        
        # Wall bounce - Y axis
        if self.y <= 0:
            self.y = -self.y
            self.vy = -self.vy
        elif self.y >= height:
            self.y = 2 * height - self.y
            self.vy = -self.vy
        
        # Clamp to bounds (safety for high velocities)
        self.x = max(0.0, min(self.x, width))
        self.y = max(0.0, min(self.y, height))
    
    def meets_quota(self) -> bool:
        """Check if agent's trust meets or exceeds their quota threshold."""
        return self.trust >= self.trust_quota
    
    def can_provide_skill_to(self, other: 'Agent') -> bool:
        """
        Check if this agent can provide what the other agent needs.
        IntEnum comparison is a single integer comparison - very fast.
        """
        return self.skill_possessed == other.skill_needed
    
    def skills_match(self, other: 'Agent') -> bool:
        """
        Check if both agents can fulfill each other's needs (mutual match).
        """
        return (
            self.skill_possessed == other.skill_needed and
            other.skill_possessed == self.skill_needed
        )
    
    def adjust_trust(self, delta: float) -> None:
        """
        Adjust trust value, clamping to [0.0, 1.0].
        
        Args:
            delta: Amount to add (positive) or subtract (negative)
        """
        self.trust = max(0.0, min(1.0, self.trust + delta))
    
    def apply_decay(self, decay_rate: float) -> None:
        """
        Apply trust decay (called periodically).
        
        Args:
            decay_rate: Multiplicative decay factor (e.g., 0.99 for 1% decay)
        """
        self.trust *= decay_rate
    
    def distance_to(self, other: 'Agent') -> float:
        """Calculate Euclidean distance to another agent."""
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)
    
    def distance_squared_to(self, other: 'Agent') -> float:
        """Calculate squared distance (faster, avoids sqrt)."""
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary for JSON serialization."""
        return {
            'agent_id': self.agent_id,
            'x': self.x,
            'y': self.y,
            'vx': self.vx,
            'vy': self.vy,
            'skill_possessed': self.skill_possessed.name,
            'skill_needed': self.skill_needed.name,
            'trust': self.trust,
            'trust_quota': self.trust_quota,
            'trust_alpha': self.trust_alpha,
            'trust_beta': self.trust_beta
        }
    
    def to_minimal_dict(self) -> dict:
        """Minimal payload for WebSocket updates."""
        return {
            'id': self.agent_id,
            'x': self.x,
            'y': self.y,
            'trust': self.trust,
            'skillPossessed': self.skill_possessed.name,
            'skillNeeded': self.skill_needed.name
        }
    
    def __hash__(self) -> int:
        return self.agent_id
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Agent):
            return NotImplemented
        return self.agent_id == other.agent_id