"""Tests for agents/environment.py: the two guarantees agents/PHASE_PLAN.md Phase B's gate
requires — determinism (same seed replays byte-identically) and parity with
human_interface/app.py's per-player mechanics when the shared pool isn't under stress.
"""

import unittest

from agents.coplayers import get_policy
from agents.environment import DEFAULT_SEVERITY, ResourcePool, ScarcityEnv
from common.actions import Action, ActionType
from common.config import START_WATER, SURVIVAL_COST, gather_yield, is_alive
from common.schema import validate_trial


def _run(scenario: str, seed: int, policy_name: str = "random") -> list[dict]:
    env = ScarcityEnv(scenario=scenario, seed=seed)
    policies = {pid: get_policy(policy_name, seed=seed + i) for i, pid in enumerate(env.player_ids)}
    obs = env.reset()
    all_rows: list[dict] = []
    done = False
    while not done:
        actions = {pid: policies[pid].act(o) for pid, o in obs.items() if env.players[pid].alive}
        obs, done, rows = env.step(actions)
        all_rows.extend(rows)
    return all_rows


def _enrich(rows: list[dict], trial_id: str = "t", source: str = "ai") -> list[dict]:
    out = []
    for row in rows:
        row = dict(row)
        row["trial_id"] = trial_id
        row["source"] = source
        row["timestamp"] = "2026-01-01T00:00:00+00:00"
        out.append(row)
    return out


class TestDeterminism(unittest.TestCase):
    def test_same_seed_replays_identically(self):
        self.assertEqual(_run("drought", seed=42), _run("drought", seed=42))

    def test_different_seeds_diverge(self):
        self.assertNotEqual(_run("drought", seed=1), _run("drought", seed=2))

    def test_replayed_logs_pass_schema_validation(self):
        validate_trial(_enrich(_run("drought", seed=7)))  # must not raise


class TestParityWithHumanApp(unittest.TestCase):
    """A single, unstressed gatherer's trajectory must match human_interface/app.py's formula
    exactly: resource[t] = resource[t-1] + gather_yield(t, scenario) - SURVIVAL_COST, alive iff
    resource >= 0.

    One player alone draws at most GATHER_NORMAL(3) or GATHER_DROUGHT(1) per round from a
    100-capacity pool with 0.4 growth — nowhere near enough to stress it (see
    environment.POOL_CAPACITY / POOL_GROWTH_RATE) — so this isolates the per-player mechanics
    from the pool addition and confirms it reduces to app.py's formula exactly.
    """

    @staticmethod
    def _expected_trajectory(scenario: str, rounds: int) -> list[tuple[float, bool]]:
        resource = float(START_WATER)
        out = []
        for r in range(1, rounds + 1):
            resource = resource + gather_yield(r, scenario) - SURVIVAL_COST
            out.append((resource, is_alive(resource)))
        return out

    def _check(self, scenario: str):
        env = ScarcityEnv(scenario=scenario, seed=0, player_ids=["SOLO"])
        obs = env.reset()
        actual: list[tuple[float, bool]] = []
        done = False
        while not done:
            actions = {}
            if env.players["SOLO"].alive:
                actions["SOLO"] = Action(type=ActionType.GATHER)
            obs, done, rows = env.step(actions)
            if rows:
                actual.append((rows[0]["resource_after"], rows[0]["alive"]))

        expected = self._expected_trajectory(scenario, env.total_rounds)
        for (exp_res, exp_alive), (act_res, act_alive) in zip(expected, actual):
            self.assertAlmostEqual(act_res, exp_res, places=6)
            self.assertEqual(act_alive, exp_alive)
            if not exp_alive:
                break

    def test_solo_always_gather_matches_app_formula_calm(self):
        self._check("calm")

    def test_solo_always_gather_matches_app_formula_drought(self):
        self._check("drought")


class TestSeverity(unittest.TestCase):
    """Phase G (PHASE_PLAN.md N1): `severity` is an ambient scarcity dial, orthogonal to the
    scripted drought-round shock, applied every round in every scenario. See the comment above
    `DEFAULT_SEVERITY` in agents/environment.py for why it isn't scoped to drought only.
    """

    def test_default_severity_matches_pre_phase_g_behaviour(self):
        pool_a = ResourcePool()
        pool_b = ResourcePool()
        pool_a.draw_and_regenerate({}, round_num=1, scenario="calm")
        pool_b.draw_and_regenerate({}, round_num=1, scenario="calm", severity=DEFAULT_SEVERITY)
        self.assertEqual(pool_a.stock, pool_b.stock)

    def test_higher_severity_regenerates_less_in_calm_scenario(self):
        # calm has no scripted drought round, so any difference here is purely `severity`'s doing.
        low = ResourcePool()
        low.stock = 50.0
        high = ResourcePool()
        high.stock = 50.0
        low.draw_and_regenerate({}, round_num=1, scenario="calm", severity=0.0)
        high.draw_and_regenerate({}, round_num=1, scenario="calm", severity=0.9)
        self.assertGreater(low.stock, high.stock)

    def test_severity_stacks_with_scripted_drought_shock(self):
        no_drought = ResourcePool()
        no_drought.stock = 50.0
        drought_round = ResourcePool()
        drought_round.stock = 50.0
        no_drought.draw_and_regenerate({}, round_num=1, scenario="drought", severity=0.5)
        drought_round.draw_and_regenerate({}, round_num=6, scenario="drought", severity=0.5)
        self.assertGreater(no_drought.stock, drought_round.stock)

    def test_scarcity_env_rejects_out_of_range_severity(self):
        with self.assertRaises(ValueError):
            ScarcityEnv(scenario="calm", seed=0, severity=1.5)

    def test_severity_flows_through_env_step(self):
        # Growth is applied *after* this round's draw is granted, so its effect only shows up in
        # the pool's stock for next round's grants — not in this round's resource_after. Start
        # below capacity (not fully drained) so the draw doesn't swallow the whole regen delta.
        env_low = ScarcityEnv(scenario="calm", seed=0, severity=0.0)
        env_high = ScarcityEnv(scenario="calm", seed=0, severity=0.9)
        for env in (env_low, env_high):
            env.reset()
            env.pool.stock = 50.0
        actions = {pid: Action(type=ActionType.GATHER) for pid in env_low.player_ids}
        env_low.step(dict(actions))
        env_high.step(dict(actions))
        self.assertGreater(env_low.pool.stock, env_high.pool.stock)


if __name__ == "__main__":
    unittest.main()
