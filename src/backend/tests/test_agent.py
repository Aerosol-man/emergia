# backend/tests/test_agent.py
import pytest
import math
from models.agent import Agent, Skill

# RUN THE TESTS LIKE THIS
'''
# Install pytest if needed
pip install pytest

# Run all tests
pytest backend/tests/test_agent.py -v

# Run specific test class
pytest backend/tests/test_agent.py::TestAgentMovement -v

# Run with coverage
pip install pytest-cov
pytest backend/tests/test_agent.py --cov=backend/models --cov-report=term-missing
'''


class TestSkillEnum:
    """Tests for the Skill IntEnum."""
    
    def test_skill_values_are_integers(self):
        """IntEnum values should be integers for fast comparison."""
        for skill in Skill:
            assert isinstance(skill.value, int)
    
    def test_skill_comparison_is_identity(self):
        """Same skills should be equal, different skills should not."""
        assert Skill.COOKING == Skill.COOKING
        assert Skill.COOKING != Skill.CODING
    
    def test_skill_random_returns_valid_skill(self):
        """random() should return a valid Skill member."""
        for _ in range(50):
            skill = Skill.random()
            assert isinstance(skill, Skill)
            assert skill in Skill
    
    def test_skill_random_pair_returns_different_skills(self):
        """random_pair() should always return two different skills."""
        for _ in range(100):
            possessed, needed = Skill.random_pair()
            assert isinstance(possessed, Skill)
            assert isinstance(needed, Skill)
            assert possessed != needed
    
    def test_skill_has_expected_members(self):
        """Verify expected skills exist."""
        expected = {'COOKING', 'CODING', 'TEACHING', 'BUILDING', 'HEALING', 'GROWING', 'TRADING', 'CRAFTING'}
        actual = {skill.name for skill in Skill}
        assert expected == actual


class TestAgentCreation:
    """Tests for Agent instantiation and factory methods."""
    
    def test_create_agent_directly(self):
        """Test direct Agent instantiation."""
        agent = Agent(
            agent_id=1,
            x=100.0,
            y=200.0,
            vx=10.0,
            vy=-5.0,
            skill_possessed=Skill.COOKING,
            skill_needed=Skill.CODING,
            trust=0.5,
            trust_quota=0.4
        )
        
        assert agent.agent_id == 1
        assert agent.x == 100.0
        assert agent.y == 200.0
        assert agent.vx == 10.0
        assert agent.vy == -5.0
        assert agent.skill_possessed == Skill.COOKING
        assert agent.skill_needed == Skill.CODING
        assert agent.trust == 0.5
        assert agent.trust_quota == 0.4
        assert agent.trust_alpha == 1.0  # Default
        assert agent.trust_beta == 1.0   # Default
    
    def test_create_random_agent(self):
        """Test factory method creates valid agent."""
        bounds = (800.0, 600.0)
        agent = Agent.create_random(agent_id=42, bounds=bounds)
        
        assert agent.agent_id == 42
        assert 0 <= agent.x <= bounds[0]
        assert 0 <= agent.y <= bounds[1]
        assert -50.0 <= agent.vx <= 50.0  # Default max_speed
        assert -50.0 <= agent.vy <= 50.0
        assert isinstance(agent.skill_possessed, Skill)
        assert isinstance(agent.skill_needed, Skill)
        assert agent.skill_possessed != agent.skill_needed
        assert 0.3 <= agent.trust <= 0.7
        assert agent.trust_quota == 0.5  # Default
    
    def test_create_random_with_custom_params(self):
        """Test factory method respects custom parameters."""
        bounds = (1000.0, 1000.0)
        agent = Agent.create_random(
            agent_id=99,
            bounds=bounds,
            max_speed=100.0,
            trust_quota=0.8
        )
        
        assert agent.agent_id == 99
        assert 0 <= agent.x <= bounds[0]
        assert 0 <= agent.y <= bounds[1]
        assert -100.0 <= agent.vx <= 100.0
        assert -100.0 <= agent.vy <= 100.0
        assert agent.trust_quota == 0.8
    
    def test_create_many_random_agents(self):
        """Stress test: create many agents without errors."""
        bounds = (800.0, 600.0)
        agents = [Agent.create_random(i, bounds) for i in range(1000)]
        
        assert len(agents) == 1000
        assert len(set(a.agent_id for a in agents)) == 1000  # All unique IDs


class TestAgentMovement:
    """Tests for position updates and wall bouncing."""
    
    def test_update_position_basic(self):
        """Test basic position update without walls."""
        agent = Agent(
            agent_id=1, x=100.0, y=100.0,
            vx=10.0, vy=20.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert agent.x == 110.0
        assert agent.y == 120.0
        assert agent.vx == 10.0  # Velocity unchanged
        assert agent.vy == 20.0
    
    def test_update_position_with_dt(self):
        """Test position update scales with dt."""
        agent = Agent(
            agent_id=1, x=100.0, y=100.0,
            vx=60.0, vy=120.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=0.5, bounds=bounds)
        
        assert agent.x == 130.0  # 100 + 60 * 0.5
        assert agent.y == 160.0  # 100 + 120 * 0.5
    
    def test_bounce_off_right_wall(self):
        """Test elastic bounce off right wall."""
        agent = Agent(
            agent_id=1, x=795.0, y=100.0,
            vx=10.0, vy=0.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert agent.x < bounds[0]  # Bounced back
        assert agent.vx == -10.0    # Velocity reversed
    
    def test_bounce_off_left_wall(self):
        """Test elastic bounce off left wall."""
        agent = Agent(
            agent_id=1, x=5.0, y=100.0,
            vx=-10.0, vy=0.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert agent.x > 0  # Bounced back
        assert agent.vx == 10.0  # Velocity reversed
    
    def test_bounce_off_top_wall(self):
        """Test elastic bounce off top wall (y=0)."""
        agent = Agent(
            agent_id=1, x=100.0, y=5.0,
            vx=0.0, vy=-10.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert agent.y > 0
        assert agent.vy == 10.0
    
    def test_bounce_off_bottom_wall(self):
        """Test elastic bounce off bottom wall."""
        agent = Agent(
            agent_id=1, x=100.0, y=595.0,
            vx=0.0, vy=10.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert agent.y < bounds[1]
        assert agent.vy == -10.0
    
    def test_corner_bounce(self):
        """Test bounce in corner (both walls)."""
        agent = Agent(
            agent_id=1, x=795.0, y=595.0,
            vx=10.0, vy=10.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert 0 <= agent.x <= bounds[0]
        assert 0 <= agent.y <= bounds[1]
        assert agent.vx == -10.0
        assert agent.vy == -10.0
    
    def test_position_stays_in_bounds_high_velocity(self):
        """Test that position is clamped even with very high velocity."""
        agent = Agent(
            agent_id=1, x=400.0, y=300.0,
            vx=10000.0, vy=10000.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        bounds = (800.0, 600.0)
        
        agent.update_position(dt=1.0, bounds=bounds)
        
        assert 0 <= agent.x <= bounds[0]
        assert 0 <= agent.y <= bounds[1]


class TestAgentTrust:
    """Tests for trust-related methods."""
    
    def test_meets_quota_true(self):
        """Agent meets quota when trust >= trust_quota."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.6, trust_quota=0.5
        )
        assert agent.meets_quota() is True
    
    def test_meets_quota_exactly(self):
        """Agent meets quota when trust == trust_quota."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        assert agent.meets_quota() is True
    
    def test_meets_quota_false(self):
        """Agent doesn't meet quota when trust < trust_quota."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.4, trust_quota=0.5
        )
        assert agent.meets_quota() is False
    
    def test_adjust_trust_increase(self):
        """Test trust increase."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        agent.adjust_trust(0.1)
        
        assert agent.trust == pytest.approx(0.6)
    
    def test_adjust_trust_decrease(self):
        """Test trust decrease."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        agent.adjust_trust(-0.2)
        
        assert agent.trust == pytest.approx(0.3)
    
    def test_adjust_trust_clamps_to_max(self):
        """Trust should not exceed 1.0."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.9, trust_quota=0.5
        )
        
        agent.adjust_trust(0.5)
        
        assert agent.trust == 1.0
    
    def test_adjust_trust_clamps_to_min(self):
        """Trust should not go below 0.0."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.1, trust_quota=0.5
        )
        
        agent.adjust_trust(-0.5)
        
        assert agent.trust == 0.0
    
    def test_apply_decay(self):
        """Test multiplicative trust decay."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        agent.apply_decay(0.9)  # 10% decay
        
        assert agent.trust == pytest.approx(0.45)
    
    def test_apply_decay_multiple_times(self):
        """Test decay compounds correctly."""
        agent = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=1.0, trust_quota=0.5
        )
        
        for _ in range(10):
            agent.apply_decay(0.9)
        
        assert agent.trust == pytest.approx(1.0 * (0.9 ** 10))


class TestAgentSkillMatching:
    """Tests for skill matching logic."""
    
    def test_can_provide_skill_to_match(self):
        """Agent can provide skill when possessed matches other's needed."""
        seller = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        buyer = Agent(
            agent_id=2, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.TEACHING, skill_needed=Skill.COOKING,
            trust=0.5, trust_quota=0.5
        )
        
        assert seller.can_provide_skill_to(buyer) is True
    
    def test_can_provide_skill_to_no_match(self):
        """Agent cannot provide skill when no match."""
        agent1 = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.TEACHING, skill_needed=Skill.BUILDING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.can_provide_skill_to(agent2) is False
    
    def test_skills_match_mutual(self):
        """Both agents can fulfill each other's needs."""
        agent1 = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.CODING, skill_needed=Skill.COOKING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.skills_match(agent2) is True
        assert agent2.skills_match(agent1) is True
    
    def test_skills_match_one_way_only(self):
        """Only one agent can provide - not a mutual match."""
        agent1 = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.TEACHING, skill_needed=Skill.COOKING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.skills_match(agent2) is False
    
    def test_skills_match_no_match(self):
        """Neither agent can provide what the other needs."""
        agent1 = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.BUILDING, skill_needed=Skill.HEALING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.skills_match(agent2) is False


class TestAgentDistance:
    """Tests for distance calculations."""
    
    def test_distance_to_same_position(self):
        """Distance to same position is 0."""
        agent1 = Agent(
            agent_id=1, x=100.0, y=100.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=100.0, y=100.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.distance_to(agent2) == 0.0
    
    def test_distance_to_horizontal(self):
        """Test horizontal distance."""
        agent1 = Agent(
            agent_id=1, x=0.0, y=0.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=100.0, y=0.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.distance_to(agent2) == 100.0
    
    def test_distance_to_vertical(self):
        """Test vertical distance."""
        agent1 = Agent(
            agent_id=1, x=0.0, y=0.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=0.0, y=50.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.distance_to(agent2) == 50.0
    
    def test_distance_to_diagonal(self):
        """Test diagonal distance (3-4-5 triangle)."""
        agent1 = Agent(
            agent_id=1, x=0.0, y=0.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=3.0, y=4.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.distance_to(agent2) == 5.0
    
    def test_distance_squared_to(self):
        """Test squared distance avoids sqrt."""
        agent1 = Agent(
            agent_id=1, x=0.0, y=0.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=3.0, y=4.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.distance_squared_to(agent2) == 25.0
    
    def test_distance_is_symmetric(self):
        """Distance from A to B equals B to A."""
        agent1 = Agent(
            agent_id=1, x=10.0, y=20.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=50.0, y=80.0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1.distance_to(agent2) == agent2.distance_to(agent1)


class TestAgentSerialization:
    """Tests for JSON serialization methods."""
    
    def test_to_dict(self):
        """Test full serialization."""
        agent = Agent(
            agent_id=1, x=100.0, y=200.0, vx=10.0, vy=-5.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.75, trust_quota=0.5,
            trust_alpha=2.0, trust_beta=3.0
        )
        
        result = agent.to_dict()
        
        assert result == {
            'agent_id': 1,
            'x': 100.0,
            'y': 200.0,
            'vx': 10.0,
            'vy': -5.0,
            'skill_possessed': 'COOKING',
            'skill_needed': 'CODING',
            'trust': 0.75,
            'trust_quota': 0.5,
            'trust_alpha': 2.0,
            'trust_beta': 3.0
        }
    
    def test_to_minimal_dict(self):
        """Test minimal serialization for WebSocket."""
        agent = Agent(
            agent_id=42, x=100.0, y=200.0, vx=10.0, vy=-5.0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.75, trust_quota=0.5
        )
        
        result = agent.to_minimal_dict()
        
        assert result == {
            'id': 42,
            'x': 100.0,
            'y': 200.0,
            'trust': 0.75,
            'skillPossessed': 'COOKING',
            'skillNeeded': 'CODING'
        }
    
    def test_to_dict_skills_are_strings(self):
        """Skills should serialize as strings, not integers."""
        agent = Agent.create_random(1, (800.0, 600.0))
        result = agent.to_dict()
        
        assert isinstance(result['skill_possessed'], str)
        assert isinstance(result['skill_needed'], str)


class TestAgentHashEquality:
    """Tests for hash and equality behavior."""
    
    def test_agents_equal_by_id(self):
        """Agents with same ID are equal regardless of other fields."""
        agent1 = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=1, x=100, y=100, vx=50, vy=50,
            skill_possessed=Skill.BUILDING, skill_needed=Skill.HEALING,
            trust=0.9, trust_quota=0.1
        )
        
        assert agent1 == agent2
    
    def test_agents_not_equal_different_id(self):
        """Agents with different IDs are not equal."""
        agent1 = Agent(
            agent_id=1, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=2, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        
        assert agent1 != agent2
    
    def test_agent_hash_consistent(self):
        """Same agent ID produces same hash."""
        agent1 = Agent(
            agent_id=42, x=0, y=0, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.5, trust_quota=0.5
        )
        agent2 = Agent(
            agent_id=42, x=100, y=100, vx=0, vy=0,
            skill_possessed=Skill.BUILDING, skill_needed=Skill.HEALING,
            trust=0.1, trust_quota=0.9
        )
        
        assert hash(agent1) == hash(agent2)
    
    def test_agents_usable_in_set(self):
        """Agents can be stored in a set."""
        agents = {
            Agent.create_random(i, (800.0, 600.0))
            for i in range(100)
        }
        
        assert len(agents) == 100
    
    def test_agents_usable_as_dict_keys(self):
        """Agents can be used as dictionary keys."""
        agent1 = Agent.create_random(1, (800.0, 600.0))
        agent2 = Agent.create_random(2, (800.0, 600.0))
        
        data = {agent1: "first", agent2: "second"}
        
        assert data[agent1] == "first"
        assert data[agent2] == "second"
    
    def test_equality_with_non_agent(self):
        """Comparing agent with non-agent returns NotImplemented."""
        agent = Agent.create_random(1, (800.0, 600.0))
        
        assert agent != "not an agent"
        assert agent != 42
        assert agent != None


class TestAgentIntegration:
    """Integration tests simulating real usage patterns."""
    
    def test_simulation_tick(self):
        """Simulate a single tick of agent updates."""
        bounds = (800.0, 600.0)
        agents = [Agent.create_random(i, bounds) for i in range(100)]
        dt = 1 / 60
        
        # Store initial positions
        initial_positions = [(a.x, a.y) for a in agents]
        
        # Update all agents
        for agent in agents:
            agent.update_position(dt, bounds)
        
        # At least some agents should have moved
        moved = sum(
            1 for i, a in enumerate(agents)
            if (a.x, a.y) != initial_positions[i]
        )
        assert moved > 0
        
        # All agents should be in bounds
        for agent in agents:
            assert 0 <= agent.x <= bounds[0]
            assert 0 <= agent.y <= bounds[1]
    
    def test_trust_transaction_scenario(self):
        """Test a complete trust transaction scenario."""
        # Seller has cooking, needs coding
        seller = Agent(
            agent_id=1, x=100, y=100, vx=0, vy=0,
            skill_possessed=Skill.COOKING, skill_needed=Skill.CODING,
            trust=0.6, trust_quota=0.5
        )
        # Buyer needs cooking, has coding
        buyer = Agent(
            agent_id=2, x=105, y=100, vx=0, vy=0,
            skill_possessed=Skill.CODING, skill_needed=Skill.COOKING,
            trust=0.7, trust_quota=0.5
        )
        
        # Check conditions
        assert seller.can_provide_skill_to(buyer)
        assert seller.meets_quota()
        assert buyer.meets_quota()
        
        # This is a mutual match - both can trade
        assert seller.skills_match(buyer)
        
        # Apply trust rewards
        seller.adjust_trust(0.05)
        buyer.adjust_trust(0.05)
        
        assert seller.trust == pytest.approx(0.65)
        assert buyer.trust == pytest.approx(0.75)
    
    def test_long_running_simulation(self):
        """Test agent behavior over many ticks."""
        bounds = (800.0, 600.0)
        agent = Agent.create_random(1, bounds, max_speed=100.0)
        dt = 1 / 60
        
        # Run for 10 simulated seconds
        for _ in range(600):
            agent.update_position(dt, bounds)
            agent.apply_decay(0.999)
        
        # Agent should still be in bounds
        assert 0 <= agent.x <= bounds[0]
        assert 0 <= agent.y <= bounds[1]
        
        # Trust should have decayed
        assert agent.trust < 0.7  # Started at max 0.7