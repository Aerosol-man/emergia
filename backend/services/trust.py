# backend/services/trust.py
from models.agent import Agent


class TrustEngine:
    def __init__(self, global_alpha: float, global_beta: float):
        self.global_alpha = float(global_alpha)
        self.global_beta = float(global_beta)

    def apply_collision_logic(self, agent1: Agent, agent2: Agent) -> dict:
        """
        Apply trust logic for collision between two agents.
        Interprets agent1 as seller, agent2 as buyer (per design doc):
          OnCollide(agent1 (seller), agent2 (buyer)) -> OnCollide(agent2, agent1)

        Returns a dict suitable for collision logging.
        """
        seller = agent1
        buyer = agent2

        # Check skill condition (seller must have what buyer needs)
        skills_match_direction = (seller.skill_possessed == buyer.skill_needed)

        # If skill doesn't match in this direction, no trust logic triggers (per doc)
        if not skills_match_direction:
            return {
                "seller": getattr(seller, "agent_id", None),
                "buyer": getattr(buyer, "agent_id", None),
                "skills_match": False,
                "case": "no_skill_match",
                "trust_delta_seller": 0.0,
                "trust_delta_buyer": 0.0,
                "trade": False,
            }

        seller_ok = (seller.trust >= seller.trust_quota)
        buyer_ok = (buyer.trust >= buyer.trust_quota)

        trust_delta_seller = 0.0
        trust_delta_buyer = 0.0
        trade = False

        # CASE 1: Neither satisfied with trust quotas -> No change
        if (not seller_ok) and (not buyer_ok):
            self._case_1_neither_meets_quota(seller, buyer)
            case = "case_1_neither_meets_quota"

        # CASE 2: Seller satisfied but buyer not -> Seller trust DOWN
        elif seller_ok and (not buyer_ok):
            trust_delta_seller = -self.global_beta
            self._case_2_seller_meets_buyer_doesnt(seller, buyer)
            case = "case_2_seller_meets_buyer_doesnt"

        # CASE 3: Buyer satisfied but seller not -> Buyer trust DOWN
        elif buyer_ok and (not seller_ok):
            trust_delta_buyer = -self.global_beta
            self._case_3_buyer_meets_seller_doesnt(buyer, seller)
            case = "case_3_buyer_meets_seller_doesnt"

        # CASE 4: Both satisfied with trust quotas (and skill match already true) -> both trust UP
        else:
            trust_delta_seller = +self.global_alpha
            trust_delta_buyer = +self.global_alpha
            self._case_4_both_meet_skills_match(seller, buyer)
            case = "case_4_both_meet_skills_match"
            trade = True

        return {
            "seller": getattr(seller, "agent_id", None),
            "buyer": getattr(buyer, "agent_id", None),
            "skills_match": True,
            "case": case,
            "trust_delta_seller": trust_delta_seller,
            "trust_delta_buyer": trust_delta_buyer,
            "trade": trade,
        }

    def _case_1_neither_meets_quota(self, agent1: Agent, agent2: Agent):
        """No trust change"""
        # Explicitly do nothing
        return

    def _case_2_seller_meets_buyer_doesnt(self, seller: Agent, buyer: Agent):
        """Seller trust DOWN"""
        seller.trust = self._clamp_trust(seller.trust - self.global_beta)

    def _case_3_buyer_meets_seller_doesnt(self, buyer: Agent, seller: Agent):
        """Buyer trust DOWN"""
        buyer.trust = self._clamp_trust(buyer.trust - self.global_beta)

    def _case_4_both_meet_skills_match(self, agent1: Agent, agent2: Agent):
        """Both trust UP"""
        agent1.trust = self._clamp_trust(agent1.trust + self.global_alpha)
        agent2.trust = self._clamp_trust(agent2.trust + self.global_alpha)

    def apply_decay(self, agents: dict[int, Agent], decay_rate: float):
        """
        Apply trust decay to all agents.

        Design doc: coefficient applied when trades are not made. The *cadence*
        (every X ticks) is controlled by the SimulationEngine; this function
        simply applies decay when called.

        decay_rate: float in [0,1], multiplicative factor (e.g. 0.99 means -1%)
        """
        decay_rate = float(decay_rate)
        if decay_rate < 0.0:
            decay_rate = 0.0
        if decay_rate > 1.0:
            decay_rate = 1.0

        for a in agents.values():
            a.trust = self._clamp_trust(a.trust * decay_rate)

    def _clamp_trust(self, trust: float) -> float:
        """Ensure trust stays in [0.0, 1.0]"""
        if trust < 0.0:
            return 0.0
        if trust > 1.0:
            return 1.0
        return trust
