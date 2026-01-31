# backend/services/collision.py
from typing import List, Tuple
from models.agent import Agent

class CollisionDetector:
    def __init__(self, collision_radius: float = 10.0):
        self.collision_radius = collision_radius
    
    def detect_collisions(self, agents: dict[int, Agent]) -> List[Tuple[int, int]]:
        """
        O(n²) pairwise distance check
        Returns list of (agent_id1, agent_id2) tuples
        """
        pass
    
    def _distance(self, agent1: Agent, agent2: Agent) -> float:
        """Calculate Euclidean distance between two agents"""
        pass