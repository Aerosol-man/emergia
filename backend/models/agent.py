# backend/models/agent.py
from dataclasses import dataclass
from typing import Optional
from enum import IntEnum, auto
import random
import math


class Skill(IntEnum):
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
        return random.choice(list(cls))

    @classmethod
    def random_pair(cls) -> tuple['Skill', 'Skill']:
        skills = list(cls)
        possessed = random.choice(skills)
        needed = random.choice([s for s in skills if s != possessed])
        return possessed, needed


@dataclass(slots=True)
class Agent:
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

    trade_count: int = 0
    last_trade_tick: int = 0
    is_custom: bool = False
    group_id: int = 0

    @classmethod
    def create_random(
        cls,
        agent_id: int,
        bounds: tuple[float, float],
        max_speed: float = 50.0,
        trust_quota: float = 0.5,
    ) -> 'Agent':
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
        self.x += self.vx * dt
        self.y += self.vy * dt

        width, height = bounds

        if self.x <= 0:
            self.x = -self.x
            self.vx = -self.vx
        elif self.x >= width:
            self.x = 2 * width - self.x
            self.vx = -self.vx

        if self.y <= 0:
            self.y = -self.y
            self.vy = -self.vy
        elif self.y >= height:
            self.y = 2 * height - self.y
            self.vy = -self.vy

        self.x = max(0.0, min(self.x, width))
        self.y = max(0.0, min(self.y, height))

    def meets_quota(self) -> bool:
        return self.trust >= self.trust_quota

    def can_provide_skill_to(self, other: 'Agent') -> bool:
        return self.skill_possessed == other.skill_needed

    def skills_match(self, other: 'Agent') -> bool:
        return self.can_provide_skill_to(other) and other.can_provide_skill_to(self)

    def adjust_trust(self, delta: float) -> None:
        self.trust = max(0.0, min(1.0, self.trust + delta))

    def apply_decay(self, decay_rate: float) -> None:
        self.trust *= decay_rate

    def distance_to(self, other: 'Agent') -> float:
        return math.sqrt(self.distance_squared_to(other))

    def distance_squared_to(self, other: 'Agent') -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "skill_possessed": self.skill_possessed.name,
            "skill_needed": self.skill_needed.name,
            "trust": self.trust,
            "trust_quota": self.trust_quota,
            "trust_alpha": self.trust_alpha,
            "trust_beta": self.trust_beta,
            "trade_count": self.trade_count,
            "last_trade_tick": self.last_trade_tick,
            "is_custom": self.is_custom,
            "group_id": self.group_id,
        }

    def to_minimal_dict(self) -> dict:
        return {
            "id": self.agent_id,
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "trust": self.trust,
            "trustQuota": self.trust_quota,
            "skillPossessed": int(self.skill_possessed),
            "skillNeeded": int(self.skill_needed),
            "tradeCount": self.trade_count,
            "isCustom": self.is_custom,
            "groupId": self.group_id,
        }

    def __eq__(self, other):
        if not isinstance(other, Agent):
            return NotImplemented
        return self.agent_id == other.agent_id

    def __hash__(self):
        return hash(self.agent_id)