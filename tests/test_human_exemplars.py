"""
Unit tests for agents/human_exemplars.py and LLM In-Context Learning steering.
"""

import unittest
from unittest.mock import patch

from agents.environment import Observation, OtherPlayerView
from agents.human_exemplars import (
    CANONICAL_HUMAN_EXEMPLARS,
    format_exemplars_prompt,
    query_human_exemplars,
)
from agents.llm_reasoning import decide
from common.actions import ActionType


def _make_obs(**overrides) -> Observation:
    defaults = dict(
        player_id="A1",
        round=8,
        total_rounds=20,
        scenario="drought",
        is_drought=True,
        own_resource=3.0,
        own_alive=True,
        received_share_last_round=0.0,
        pool_stock=10.0,
        pool_capacity=30.0,
        others=(OtherPlayerView(player_id="A2", alive=True, last_action=ActionType.GATHER, last_action_target=None),),
    )
    defaults.update(overrides)
    return Observation(**defaults)


class TestHumanExemplars(unittest.TestCase):
    def test_query_human_exemplars_returns_exemplars(self):
        obs = _make_obs()
        exemplars = query_human_exemplars(obs, limit=2)
        self.assertIsInstance(exemplars, list)
        self.assertGreaterEqual(len(exemplars), 1)
        self.assertIn("action", exemplars[0])
        self.assertIn("context", exemplars[0])

    def test_fallback_canonical_exemplars(self):
        # Querying a non-existent database path returns canonical fallback exemplars
        exemplars = query_human_exemplars(db_path="non_existent.db", limit=2)
        self.assertEqual(len(exemplars), 2)
        self.assertEqual(exemplars[0]["action"]["action_type"], "share")

    def test_format_exemplars_prompt(self):
        exemplars = CANONICAL_HUMAN_EXEMPLARS[:2]
        prompt = format_exemplars_prompt(exemplars)
        self.assertIn("OBSERVED HUMAN BEHAVIOR DEMONSTRATIONS", prompt)
        self.assertIn("Human Demonstration #1", prompt)
        self.assertIn("share", prompt)

    def test_decide_with_use_human_exemplars(self):
        obs = _make_obs()
        with patch("agents.llm_reasoning.complete", return_value={"action_type": "share", "target": "A2", "amount": 1}):
            action, meta = decide(obs, use_human_exemplars=True, n_exemplars=2)
            self.assertEqual(action.type, ActionType.SHARE)
            self.assertTrue(meta["use_human_exemplars"])
            self.assertGreaterEqual(meta["exemplars_count"], 1)
            self.assertFalse(meta["llm_parse_failure"])


if __name__ == "__main__":
    unittest.main()
