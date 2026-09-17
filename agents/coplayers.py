"""Fixed co-player policies — the deliverable this track owes `group1-human-study` per
INTEGRATION_ISSUES.md Blocker 1. Every session has `common.config.NUM_PLAYERS` players; the focal
player is human in one arm and an AI agent in the other, and the remaining players run one of these
frozen policies so both arms see identical co-player behaviour under a shared seed.

Interface every policy implements: `act(observation) -> Action`. Keep it that narrow — a policy
must not read anything not on Observation (no peeking at another player's true resource, no
reaching into the environment's RNG), or the human and AI arms stop being a matched comparison.
"""

from __future__ import annotations

import random
from typing import Protocol

from agents.environment import Observation
from common.actions import Action, ActionType, Message, MessageKind
from common.config import SURVIVAL_COST


class CoPlayerPolicy(Protocol):
    def act(self, obs: Observation) -> Action: ...


class Cooperator:
    """Gathers when its own stock is fine, shares a fixed amount with an arbitrary alive other
    player once it has a comfortable surplus, and falls back to gathering when critical."""

    def __init__(self, seed: int = 0, share_amount: int = 1):
        self.rng = random.Random(seed)
        self.share_amount = share_amount

    def act(self, obs: Observation) -> Action:
        if obs.own_resource <= SURVIVAL_COST:
            return Action(type=ActionType.GATHER)

        alive_others = [o for o in obs.others if o.alive]
        if alive_others and obs.own_resource > SURVIVAL_COST * 2:
            # Deliberately picks *someone*, not "whoever looks worst off" — a policy can't see
            # another player's true resource (Observation carries no such field), only that the
            # study intends to make hidden stock the thing deception is about.
            target = self.rng.choice(alive_others)
            return Action(
                type=ActionType.SHARE,
                target=target.player_id,
                amount=self.share_amount,
                message=Message(
                    kind=MessageKind.PROMISE_SHARE,
                    value=self.share_amount,
                    target=target.player_id,
                    surface="Here, take some — we'll all need water later.",
                ),
            )
        return Action(type=ActionType.GATHER)


class FreeRider:
    """Always gathers, never shares. Hoards only once the visible pool has hit zero, since
    gathering from an empty pool is pointless."""

    def __init__(self, seed: int = 0):
        pass  # deterministic policy, no randomness needed — seed accepted for interface parity

    def act(self, obs: Observation) -> Action:
        if obs.pool_stock <= 0:
            return Action(type=ActionType.HOARD)
        return Action(type=ActionType.GATHER)


class TitForTat:
    """Cooperative by default; if nobody shared with it last round, it withholds this round — a
    group-scale simplification of pairwise tit-for-tat (there's no single "partner" in a 5-player
    commons, so reciprocity here is "did *anyone* share with me," not "did this specific player").
    """

    def __init__(self, seed: int = 0, share_amount: int = 1):
        self.rng = random.Random(seed)
        self.share_amount = share_amount

    def act(self, obs: Observation) -> Action:
        if obs.round > 1 and obs.received_share_last_round <= 0:
            return Action(type=ActionType.GATHER)  # withhold this round

        alive_others = [o for o in obs.others if o.alive]
        if alive_others and obs.own_resource > SURVIVAL_COST * 2:
            target = self.rng.choice(alive_others)
            return Action(type=ActionType.SHARE, target=target.player_id, amount=self.share_amount)
        return Action(type=ActionType.GATHER)


class RandomPolicy:
    """Uniform-random valid action. Used for smoke tests, determinism tests, and as a null
    baseline — not a serious behavioural model."""

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def act(self, obs: Observation) -> Action:
        alive_others = [o for o in obs.others if o.alive]
        choices: list[ActionType] = [ActionType.GATHER, ActionType.HOARD, ActionType.SKIP]
        if alive_others and obs.own_resource > 1:
            choices.append(ActionType.SHARE)
        action_type = self.rng.choice(choices)
        if action_type == ActionType.SHARE:
            target = self.rng.choice(alive_others)
            return Action(type=ActionType.SHARE, target=target.player_id, amount=1)
        return Action(type=action_type)


POLICIES: dict[str, type] = {
    "cooperator": Cooperator,
    "free_rider": FreeRider,
    "tit_for_tat": TitForTat,
    "random": RandomPolicy,
}


def get_policy(name: str, seed: int = 0) -> CoPlayerPolicy:
    if name not in POLICIES:
        raise ValueError(f"unknown co-player policy {name!r}, must be one of {sorted(POLICIES)}")
    return POLICIES[name](seed=seed)
