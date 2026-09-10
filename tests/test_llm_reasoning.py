"""Fast tests for agents/llm_reasoning.py's parsing and retry logic. No live API calls —
agents.llm_reasoning.complete is mocked throughout. Live verification is a manual step
(agents/llm_trial.py), not part of this suite — see tests/test_llm_client.py's docstring for why.
"""

import unittest
from unittest.mock import patch

from agents.environment import Observation, OtherPlayerView
from agents.llm_client import LLMCompletionError
from agents.llm_reasoning import _parse_action, decide, render_observation
from common.actions import ActionType


def _make_observation(**overrides) -> Observation:
    defaults = dict(
        player_id="A1",
        round=6,
        total_rounds=10,
        scenario="drought",
        is_drought=True,
        own_resource=3.0,
        own_alive=True,
        received_share_last_round=0.0,
        pool_stock=12.0,
        pool_capacity=100.0,
        others=(
            OtherPlayerView(player_id="A2", alive=True, last_action=ActionType.GATHER, last_action_target=None),
        ),
    )
    defaults.update(overrides)
    return Observation(**defaults)


class TestRenderObservation(unittest.TestCase):
    def test_mentions_drought_when_relevant(self):
        text = render_observation(_make_observation(is_drought=True))
        self.assertIn("drought", text.lower())

    def test_omits_drought_warning_when_not_drought(self):
        text = render_observation(_make_observation(is_drought=False))
        self.assertNotIn("drought round", text.lower())

    def test_mentions_pool_level(self):
        text = render_observation(_make_observation(pool_stock=42.0, pool_capacity=100.0))
        self.assertIn("42.0", text)

    def test_mentions_other_players(self):
        text = render_observation(_make_observation())
        self.assertIn("A2", text)


class TestParseAction(unittest.TestCase):
    def test_valid_gather(self):
        action = _parse_action({"action_type": "gather"})
        self.assertEqual(action.type, ActionType.GATHER)

    def test_valid_share_with_message(self):
        action = _parse_action(
            {
                "action_type": "share",
                "target": "A2",
                "amount": 1,
                "message": {"kind": "promise_share", "value": 1, "target": "A2", "surface": "here"},
            }
        )
        self.assertEqual(action.type, ActionType.SHARE)
        self.assertEqual(action.target, "A2")
        self.assertEqual(action.message.surface, "here")

    def test_invalid_enum_raises_value_error(self):
        with self.assertRaises(ValueError):
            _parse_action({"action_type": "teleport"})

    def test_share_without_target_raises_via_action_validate(self):
        with self.assertRaises(ValueError):
            _parse_action({"action_type": "share", "amount": 1})

    def test_missing_action_type_raises_key_error(self):
        with self.assertRaises(KeyError):
            _parse_action({})


class TestDecideRetryLogic(unittest.TestCase):
    def test_succeeds_on_first_attempt(self):
        with patch("agents.llm_reasoning.complete", return_value={"action_type": "gather"}) as mock_complete:
            action, meta = decide(_make_observation())
        self.assertEqual(action.type, ActionType.GATHER)
        self.assertFalse(meta["llm_parse_failure"])
        self.assertEqual(meta["parse_attempts"], 1)
        mock_complete.assert_called_once()

    def test_retries_once_after_bad_json_then_succeeds(self):
        responses = [LLMCompletionError("bad json"), {"action_type": "hoard"}]

        def fake_complete(*args, **kwargs):
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch("agents.llm_reasoning.complete", side_effect=fake_complete) as mock_complete:
            action, meta = decide(_make_observation())
        self.assertEqual(action.type, ActionType.HOARD)
        self.assertFalse(meta["llm_parse_failure"])
        self.assertEqual(meta["parse_attempts"], 2)
        self.assertEqual(mock_complete.call_count, 2)

    def test_retries_once_after_schema_mismatch_then_succeeds(self):
        """Distinct from a bad-JSON failure: this is syntactically valid JSON that doesn't parse
        into our Action shape (e.g. share with no target) — the case the retry loop's
        "validation error appended" wording specifically describes.
        """
        responses = [{"action_type": "share"}, {"action_type": "skip"}]  # first is missing target

        def fake_complete(*args, **kwargs):
            return responses.pop(0)

        with patch("agents.llm_reasoning.complete", side_effect=fake_complete):
            action, meta = decide(_make_observation())
        self.assertEqual(action.type, ActionType.SKIP)
        self.assertFalse(meta["llm_parse_failure"])
        self.assertEqual(meta["parse_attempts"], 2)

    def test_falls_back_to_skip_after_two_failures(self):
        with patch("agents.llm_reasoning.complete", side_effect=LLMCompletionError("down")):
            action, meta = decide(_make_observation())
        self.assertEqual(action.type, ActionType.SKIP)
        self.assertTrue(meta["llm_parse_failure"])
        self.assertEqual(meta["parse_attempts"], 2)
        self.assertIn("down", meta["parse_error"])

    def test_never_raises_even_on_total_failure(self):
        """The core Phase E guarantee: 'parse failures are data, not crashes.'"""
        with patch("agents.llm_reasoning.complete", side_effect=RuntimeError("totally unexpected")):
            # Only LLMCompletionError/KeyError/ValueError/TypeError are caught by design — an
            # unexpected exception type SHOULD still propagate, since silently swallowing
            # arbitrary errors would hide real bugs. Confirm that boundary explicitly.
            with self.assertRaises(RuntimeError):
                decide(_make_observation())

    def test_usage_is_captured_even_on_final_failure(self):
        def fake_complete(messages, schema=None, *, provider=None, model=None, temperature=0.4, usage=None):
            if usage is not None:
                usage["prompt_tokens"] = 10
                usage["completion_tokens"] = 5
                usage["model"] = "fake-model"
                usage["provider"] = "fake"
            raise LLMCompletionError("still invalid")

        with patch("agents.llm_reasoning.complete", side_effect=fake_complete):
            action, meta = decide(_make_observation())
        self.assertTrue(meta["llm_parse_failure"])
        self.assertEqual(meta["prompt_tokens"], 10)
        self.assertEqual(meta["completion_tokens"], 5)


if __name__ == "__main__":
    unittest.main()
