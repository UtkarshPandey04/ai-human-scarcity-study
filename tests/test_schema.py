"""Self-tests for common/schema.py — this is what "make validate" / "python tasks.py validate"
actually runs. Run directly with `python -m unittest tests.test_schema -v` or via tasks.py.

Includes a row shaped exactly like what human_interface/logging_utils.log_action() currently
produces, so a schema change that breaks Group 1's already-shipped logs fails loudly here instead
of surfacing during Week 8 analysis.
"""

import unittest

from common.schema import SchemaError, validate_row, validate_trial


def make_row(**overrides):
    row = {
        "trial_id": "drought_ai_001",
        "source": "ai",
        "agent_id": "A1",
        "round": 1,
        "scenario": "drought",
        "action_type": "gather",
        "target_agent": None,
        "message_sent": None,
        "resource_before": 5,
        "resource_after": 6,
        "alive": True,
        "timestamp": "2026-09-03T10:00:00Z",
    }
    row.update(overrides)
    return row


class ValidRowsPass(unittest.TestCase):
    def test_minimal_valid_row(self):
        validate_row(make_row())  # must not raise

    def test_group1_shipped_row_shape(self):
        """Matches exactly what human_interface/logging_utils.log_action() emits today,
        including its timezone-aware ISO timestamp — this is the Gate A regression check.
        """
        row = {
            "trial_id": "drought_human_ab12cd",
            "source": "human",
            "agent_id": "PAB12",
            "round": 1,
            "scenario": "drought",
            "action_type": "gather",
            "target_agent": None,
            "message_sent": None,
            "resource_before": 5,
            "resource_after": 6,
            "alive": True,
            "timestamp": "2026-09-03T10:32:00.123456+00:00",
        }
        validate_row(row)  # must not raise

    def test_share_with_target_and_message(self):
        row = make_row(
            action_type="share",
            target_agent="A2",
            message_sent="Take less today, I'll pay you back",
            resource_before=4,
            resource_after=3,
        )
        validate_row(row)

    def test_meta_absent_is_fine(self):
        validate_row(make_row())  # no "meta" key at all

    def test_meta_present_and_valid(self):
        row = make_row(
            meta={
                "severity": 0.7,
                "seed": 42,
                "arm": "hybrid",
                "model": "some-model",
                "decision_latency_ms": 1200,
                "claim": {"kind": "claim_stock", "value": 1, "target": "A2", "surface": "only 1 left"},
            }
        )
        validate_row(row)


class MalformedRowsFail(unittest.TestCase):
    def test_missing_field(self):
        row = make_row()
        del row["resource_after"]
        with self.assertRaises(SchemaError):
            validate_row(row)

    def test_wrong_type(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(round="six"))

    def test_bad_source(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(source="robot"))

    def test_bad_action_type(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(action_type="teleport"))

    def test_bad_scenario(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(scenario="flood"))

    def test_round_below_one(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(round=0))

    def test_share_without_target(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(action_type="share", target_agent=None))

    def test_communicate_without_target(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(action_type="communicate", target_agent=None))

    def test_bad_meta_arm(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(meta={"arm": "quantum"}))

    def test_bad_meta_severity_out_of_range(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(meta={"severity": 1.5}))

    def test_bad_claim_kind(self):
        with self.assertRaises(SchemaError):
            validate_row(make_row(meta={"claim": {"kind": "lie"}}))

    def test_not_a_dict(self):
        with self.assertRaises(SchemaError):
            validate_row(["not", "a", "dict"])


class TrialInvariants(unittest.TestCase):
    def test_valid_trial(self):
        rows = [
            make_row(agent_id="A1", round=1),
            make_row(agent_id="A1", round=2),
            make_row(agent_id="A2", round=1),
        ]
        validate_trial(rows)

    def test_empty_trial_fails(self):
        with self.assertRaises(SchemaError):
            validate_trial([])

    def test_round_going_backwards_fails(self):
        rows = [
            make_row(agent_id="A1", round=2),
            make_row(agent_id="A1", round=1),
        ]
        with self.assertRaises(SchemaError):
            validate_trial(rows)

    def test_action_after_death_fails(self):
        rows = [
            make_row(agent_id="A1", round=1, alive=False),
            make_row(agent_id="A1", round=2, alive=True),
        ]
        with self.assertRaises(SchemaError):
            validate_trial(rows)


if __name__ == "__main__":
    unittest.main()
