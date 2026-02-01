# backend/services/collision.py
from typing import List, Tuple, Dict, Set
from collections import defaultdict
from models.agent import Agent
import math


class SpatialHashGrid:
    """
    Spatial hash grid for O(n) average-case collision detection.
    Divides space into cells; only checks agents in same/neighboring cells.
    """
    
    __slots__ = ('cell_size', 'inv_cell_size', 'grid')
    
    def __init__(self, cell_size: float):
        self.cell_size = cell_size
        self.inv_cell_size = 1.0 / cell_size  # Multiply instead of divide
        self.grid: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    
    def clear(self):
        self.grid.clear()
    
    def _hash(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to cell coordinates."""
        return (int(x * self.inv_cell_size), int(y * self.inv_cell_size))
    
    def insert(self, agent_id: int, x: float, y: float):
        """Insert agent into grid cell."""
        self.grid[self._hash(x, y)].append(agent_id)
    
    def get_nearby(self, x: float, y: float) -> List[int]:
        """Get all agent IDs in this cell and 8 neighboring cells."""
        cx, cy = self._hash(x, y)
        nearby = []
        # Check 3x3 neighborhood
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell = (cx + dx, cy + dy)
                if cell in self.grid:
                    nearby.extend(self.grid[cell])
        return nearby


class CollisionDetector:
    """
    Optimized collision detector using spatial hashing.
    
    Time complexity: O(n) average case, O(n²) worst case (all agents clustered)
    Space complexity: O(n)
    """
    
    __slots__ = ('collision_radius', 'collision_radius_sq', 'grid')
    
    def __init__(self, collision_radius: float = 50.0):
        self.collision_radius = collision_radius
        self.collision_radius_sq = collision_radius * collision_radius
        # Cell size should be >= collision diameter for correctness
        self.grid = SpatialHashGrid(cell_size=collision_radius * 2)
    
    def detect_collisions(self, agents: Dict[int, Agent]) -> List[Tuple[int, int]]:
        """
        Detect all colliding pairs using spatial hashing.
        Returns list of (agent_id1, agent_id2) tuples where id1 < id2.
        """
        if len(agents) < 2:
            return []
        
        # Rebuild grid (faster than incremental updates for moving agents)
        self.grid.clear()
        for agent_id, agent in agents.items():
            self.grid.insert(agent_id, agent.x, agent.y)
        
        collisions: List[Tuple[int, int]] = []
        checked: Set[Tuple[int, int]] = set()
        radius_sq = self.collision_radius_sq
        
        for agent_id, agent in agents.items():
            ax, ay = agent.x, agent.y
            
            for other_id in self.grid.get_nearby(ax, ay):
                if other_id <= agent_id:
                    continue
                    
                pair = (agent_id, other_id)
                if pair in checked:
                    continue
                checked.add(pair)
                
                other = agents[other_id]
                dx = other.x - ax
                dy = other.y - ay
                
                # Squared distance comparison (avoids sqrt)
                if dx * dx + dy * dy <= radius_sq:
                    collisions.append(pair)
        
        return collisions
    
    def detect_collisions_fast(self, agents: Dict[int, Agent]) -> List[Tuple[int, int]]:
        """
        Even faster version - no duplicate checking set needed.
        Only processes each pair once by cell traversal order.
        """
        if len(agents) < 2:
            return []
        
        self.grid.clear()
        for agent_id, agent in agents.items():
            self.grid.insert(agent_id, agent.x, agent.y)
        
        collisions: List[Tuple[int, int]] = []
        radius_sq = self.collision_radius_sq
        
        # Process each cell once
        for cell_agents in self.grid.grid.values():
            n = len(cell_agents)
            if n < 2:
                continue
            
            # Check pairs within same cell
            for i in range(n):
                id1 = cell_agents[i]
                a1 = agents[id1]
                ax, ay = a1.x, a1.y
                
                for j in range(i + 1, n):
                    id2 = cell_agents[j]
                    a2 = agents[id2]
                    dx = a2.x - ax
                    dy = a2.y - ay
                    
                    if dx * dx + dy * dy <= radius_sq:
                        collisions.append((min(id1, id2), max(id1, id2)))
        
        # Cross-cell checks (right, bottom-right, bottom, bottom-left neighbors)
        for (cx, cy), cell_agents in list(self.grid.grid.items()):
            for dx, dy in ((1, 0), (1, 1), (0, 1), (-1, 1)):
                neighbor = (cx + dx, cy + dy)
                if neighbor not in self.grid.grid:
                    continue
                
                neighbor_agents = self.grid.grid[neighbor]
                for id1 in cell_agents:
                    a1 = agents[id1]
                    ax, ay = a1.x, a1.y
                    
                    for id2 in neighbor_agents:
                        a2 = agents[id2]
                        ddx = a2.x - ax
                        ddy = a2.y - ay
                        
                        if ddx * ddx + ddy * ddy <= radius_sq:
                            collisions.append((min(id1, id2), max(id1, id2)))
        
        return collisions


# For very large simulations, consider this numpy-accelerated version
class NumpyCollisionDetector:
    """
    NumPy-accelerated collision detection for large agent counts (1000+).
    Uses vectorized distance calculations with spatial binning.
    """
    
    def __init__(self, collision_radius: float = 10.0):
        self.collision_radius = collision_radius
        self.collision_radius_sq = collision_radius * collision_radius
    
    def detect_collisions(self, agents: Dict[int, Agent]) -> List[Tuple[int, int]]:
        import numpy as np
        
        if len(agents) < 2:
            return []
        
        ids = list(agents.keys())
        n = len(ids)
        
        # Vectorized position extraction
        positions = np.array([(agents[i].x, agents[i].y) for i in ids], dtype=np.float32)
        
        # For smaller counts, brute force with numpy is actually fast
        if n < 500:
            # Compute all pairwise squared distances
            diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
            dist_sq = np.sum(diff ** 2, axis=2)
            
            # Find colliding pairs (upper triangle only)
            i_indices, j_indices = np.where(
                (dist_sq <= self.collision_radius_sq) & 
                (np.triu(np.ones((n, n), dtype=bool), k=1))
            )
            
            return [(ids[i], ids[j]) for i, j in zip(i_indices, j_indices)]
        
        # For larger counts, use scipy's KDTree
        from scipy.spatial import cKDTree
        
        tree = cKDTree(positions)
        pairs = tree.query_pairs(r=self.collision_radius)
        
        return [(ids[i], ids[j]) for i, j in pairs]