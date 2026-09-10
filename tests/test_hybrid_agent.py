"""Fast tests for agents/hybrid_agent.py. No live LLM calls and no real RL checkpoint — the RL
side is a MagicMock standing in for a loaded stable_baselines3.PPO model, the LLM side is a
patched agents.hybrid_agent.llm_decide. See tests/test_llm_client.py's docstring for why this
suite must never depend on live keys or real model files.
"""

import unittest
from unittest.mock import MagicMock, patch

from agents.environment import Observation, OtherPlayerView
from agents.hybrid_agent import ARMS, HybridAgent, is_social_decision
from agents.rl_policy import LEARNER_ACTIONS
from common.actions import Action, ActionType
from common.config import SURVIVAL_COST


def _make_observation(**overrides) -> Observation:
    defaults = dict(
        player_id="A1",
        round=3,
        total_rounds=10,
        scenario="calm",
        is_drought=False,
        own_resource=10.0,
        own_alive=True,
        received_share_last_round=0.0,
        pool_stock=80.0,
        pool_capacity=100.0,
        others=(
            OtherPlayerView(player_id="A2", alive=True, last_action=None, last_action_target=None),
        ),
    )
    defaults.update(overrides)
    return Observation(**defaults)


class TestIsSocialDecision(unittest.TestCase):
    def test_false_when_no_alive_others(self):
        obs = _make_observation(own_resource=1.0, others=())
        self.assertFalse(is_social_decision(obs))

    def test_false_when_comfortable_and_calm_and_no_reciprocity(self):
        obs = _make_observation(own_resource=100.0, is_drought=False, received_share_last_round=0.0)
        self.assertFalse(is_social_decision(obs))

    def test_true_when_under_resource_pressure(self):
        obs = _make_observation(own_resource=SURVIVAL_COST * 2, is_drought=False)
        self.assertTrue(is_social_decision(obs))

    def test_true_during_drought_even_if_comfortable(self):
        obs = _make_observation(own_resource=100.0, is_drought=True)
        self.assertTrue(is_social_decision(obs))

    def test_true_on_reciprocity_opportunity(self):
        obs = _make_observation(own_resource=100.0, is_drought=False, received_share_last_round=2.0)
        self.assertTrue(is_social_decision(obs))


class TestHybridAgentConstruction(unittest.TestCase):
    def test_invalid_arm_raises(self):
        with self.assertRaises(ValueError):
            HybridAgent(arm="not_a_real_arm")

    def test_rl_only_requires_rl_model(self):
        with self.assertRaises(ValueError):
            HybridAgent(arm="rl_only", rl_model=None)

    def test_hybrid_requires_rl_model(self):
        with self.assertRaises(ValueError):
            HybridAgent(arm="hybrid", rl_model=None)

    def test_llm_only_does_not_require_rl_model(self):
        HybridAgent(arm="llm_only", rl_model=None)  # must not raise

    def test_all_declared_arms_are_constructible_with_a_model(self):
        fake_model = MagicMock()
        for arm in ARMS:
            with self.subTest(arm=arm):
                HybridAgent(arm=arm, rl_model=fake_model)  # must not raise


class TestHybridAgentDecide(unittest.TestCase):
    def setUp(self):
        self.fake_rl_model = MagicMock()
        gather_idx = LEARNER_ACTIONS.index(ActionType.GATHER)
        self.fake_rl_model.predict.return_value = (gather_idx, None)

    def test_rl_only_always_uses_rl(self):
        agent = HybridAgent(arm="rl_only", rl_model=self.fake_rl_model)
        social_obs = _make_observation(is_drought=True)  # would be "social" under hybrid routing
        action, meta = agent.decide(social_obs)
        self.assertEqual(meta["decision_source"], "rl")
        self.assertEqual(action.type, ActionType.GATHER)
        self.fake_rl_model.predict.assert_called_once()

    def test_llm_only_always_uses_llm(self):
        with patch(
            "agents.hybrid_agent.llm_decide",
            return_value=(Action(type=ActionType.HOARD), {"llm_parse_failure": False, "parse_attempts": 1}),
        ) as mock_llm:
            agent = HybridAgent(arm="llm_only", rl_model=None)
            calm_obs = _make_observation(own_resource=100.0, is_drought=False)  # not "social"
            action, meta = agent.decide(calm_obs)
        self.assertEqual(meta["decision_source"], "llm")
        self.assertEqual(action.type, ActionType.HOARD)
        mock_llm.assert_called_once()
        self.fake_rl_model.predict.assert_not_called()

    def test_hybrid_routes_social_round_to_llm(self):
        with patch(
            "agents.hybrid_agent.llm_decide",
            return_value=(Action(type=ActionType.SHARE, target="A2", amount=1), {"llm_parse_failure": False}),
        ) as mock_llm:
            agent = HybridAgent(arm="hybrid", rl_model=self.fake_rl_model)
            social_obs = _make_observation(is_drought=True)
            action, meta = agent.decide(social_obs)
        self.assertEqual(meta["decision_source"], "llm")
        mock_llm.assert_called_once()
        self.fake_rl_model.predict.assert_not_called()

    def test_hybrid_routes_non_social_round_to_rl(self):
        with patch("agents.hybrid_agent.llm_decide") as mock_llm:
            agent = HybridAgent(arm="hybrid", rl_model=self.fake_rl_model)
            calm_obs = _make_observation(own_resource=100.0, is_drought=False, received_share_last_round=0.0)
            action, meta = agent.decide(calm_obs)
        self.assertEqual(meta["decision_source"], "rl")
        self.fake_rl_model.predict.assert_called_once()
        mock_llm.assert_not_called()

    def test_hybrid_meta_always_carries_decision_source(self):
        with patch("agents.hybrid_agent.llm_decide", return_value=(Action(type=ActionType.SKIP), {})):
            agent = HybridAgent(arm="hybrid", rl_model=self.fake_rl_model)
            for obs in (_make_observation(is_drought=True), _make_observation(own_resource=100.0)):
                _, meta = agent.decide(obs)
                self.assertIn(meta["decision_source"], ("rl", "llm"))


if __name__ == "__main__":
    unittest.main()
