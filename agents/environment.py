"""Shared-pool scarcity environment — the core simulation AI trials run against.

Design choice, from INTEGRATION_ISSUES.md Blocker 3 (grid or no grid): **no grid.**
`human_interface/app.py` renders no grid and `move`/`hoard` are no-ops there, so a spatial layer
would be pure fiction on the human side of the study. Instead this environment adds the one thing
`app.py` is missing that the whole study actually depends on: a resource pool that players
collectively draw from and can collectively deplete — a real commons, not five independent
per-agent counters. See agents/PHASE_PLAN.md Phase B for the reasoning, and revisit this file if
the team decides otherwise.

Per-player mechanics (gather/share/hoard/skip numbers, survival cost, death rule) match
`human_interface/app.py` exactly whenever the shared pool isn't under stress — see
tests/test_environment.py::TestParityWithHumanApp. Only when collective draw would exceed
available pool stock does an agent's actual gather yield fall below common.config.gather_yield()'s
value; that shortfall *is* the scarcity signal the whole study is trying to elicit — it's an
emergent tragedy-of-the-commons on top of the scripted drought event, not a replacement for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from common.actions import Action, ActionType
from common.config import (
    SCENARIOS,
    START_WATER,
    SURVIVAL_COST,
    gather_yield,
    is_alive,
    is_drought,
)

# Shared-pool dynamics. Capacity and growth are chosen so that if every player gathers every round
# at the normal (non-drought) yield, collective demand exceeds the pool's maximum possible
# regeneration (g * K / 4 = 0.4 * 100 / 4 = 10, versus a full-defection draw of 5 players *
# GATHER_NORMAL(3) = 15) — i.e. full defection is unsustainable and drains the pool toward 0. That
# is the whole point of a commons: partial cooperation (hoarding/sharing instead of always
# gathering) is what keeps the pool alive. See agents/PHASE_PLAN.md Phase B for the derivation.
POOL_CAPACITY = 100.0
POOL_GROWTH_RATE = 0.4
DROUGHT_GROWTH_MULTIPLIER = 0.3  # cuts regeneration ~70%, matching the roadmap's stated severity


@dataclass
class PlayerState:
    player_id: str
    resource: float = field(default_factory=lambda: float(START_WATER))
    alive: bool = True
    last_action: ActionType | None = None
    last_action_target: str | None = None
    received_share_last_round: float = 0.0  # for reciprocity-based co-player policies


@dataclass(frozen=True)
class OtherPlayerView:
    """What a player is allowed to see about another player — never their true resource level.
    Hidden stock is what makes deception possible; see ACTIONS.md's Message slot.
    """

    player_id: str
    alive: bool
    last_action: ActionType | None
    last_action_target: str | None


@dataclass(frozen=True)
class Observation:
    player_id: str
    round: int
    total_rounds: int
    scenario: str
    is_drought: bool
    own_resource: float
    own_alive: bool
    received_share_last_round: float
    pool_stock: float
    pool_capacity: float
    others: tuple[OtherPlayerView, ...]


class ResourcePool:
    """The shared, depletable water source. Logistic regeneration: growth slows as the pool
    approaches capacity and collapses toward 0 under sustained over-draw — the mechanic that makes
    over-harvesting genuinely costly rather than a stylistic flourish.
    """

    def __init__(self, capacity: float = POOL_CAPACITY, growth_rate: float = POOL_GROWTH_RATE):
        self.capacity = capacity
        self.growth_rate = growth_rate
        self.stock = capacity

    def draw_and_regenerate(
        self, requested: dict[str, float], round_num: int, scenario: str
    ) -> dict[str, float]:
        """Attempt to satisfy every player's requested draw from current stock, then regenerate.

        If the pool can't cover total demand, every requester is scaled down proportionally —
        nobody is arbitrarily prioritized. Returns actual granted amount per player_id (only for
        players present in `requested`).
        """
        total_requested = sum(requested.values())
        if total_requested <= 0:
            granted = {pid: 0.0 for pid in requested}
        else:
            scale = min(1.0, self.stock / total_requested)
            granted = {pid: amount * scale for pid, amount in requested.items()}

        self.stock = max(0.0, self.stock - sum(granted.values()))

        growth = self.growth_rate
        if is_drought(round_num, scenario):
            growth *= DROUGHT_GROWTH_MULTIPLIER
        self.stock += growth * self.stock * (1 - self.stock / self.capacity)
        self.stock = min(self.capacity, max(0.0, self.stock))

        return granted


class ScarcityEnv:
    """Runs one trial: `reset()` then repeated `step(actions)` until every round is played or
    every player has died. See agents/scenarios.py for what `scenario` values mean.
    """

    def __init__(self, scenario: str, seed: int, player_ids: list[str] | None = None):
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario {scenario!r}, must be one of {SCENARIOS}")
        from agents.scenarios import SCENARIO_CONFIG  # local import: avoids a circular import

        self.scenario = scenario
        self.seed = seed
        self.player_ids = list(player_ids) if player_ids else [f"A{i + 1}" for i in range(5)]
        self.total_rounds = SCENARIO_CONFIG[scenario].total_rounds
        self.round = 0
        self.pool = ResourcePool()
        self.players: dict[str, PlayerState] = {
            pid: PlayerState(player_id=pid) for pid in self.player_ids
        }

    def reset(self) -> dict[str, Observation]:
        self.pool = ResourcePool()
        self.players = {pid: PlayerState(player_id=pid) for pid in self.player_ids}
        self.round = 1
        return self._observations()

    def _observations(self) -> dict[str, Observation]:
        obs: dict[str, Observation] = {}
        for pid, state in self.players.items():
            others = tuple(
                OtherPlayerView(
                    player_id=other.player_id,
                    alive=other.alive,
                    last_action=other.last_action,
                    last_action_target=other.last_action_target,
                )
                for other in self.players.values()
                if other.player_id != pid
            )
            obs[pid] = Observation(
                player_id=pid,
                round=self.round,
                total_rounds=self.total_rounds,
                scenario=self.scenario,
                is_drought=is_drought(self.round, self.scenario),
                own_resource=state.resource,
                own_alive=state.alive,
                received_share_last_round=state.received_share_last_round,
                pool_stock=self.pool.stock,
                pool_capacity=self.pool.capacity,
                others=others,
            )
        return obs

    def step(self, actions: dict[str, Action]) -> tuple[dict[str, Observation], bool, list[dict]]:
        """Advance one round. `actions` should have an entry for every alive player; a missing
        entry is treated as `skip`. Returns `(next_observations, done, log_rows)` where log_rows
        are schema-shaped dicts missing only `trial_id` / `source` / `timestamp` / `meta`, which
        the caller fills in (see agents/smoke_random.py).
        """
        if self.round < 1:
            raise RuntimeError("call reset() before step()")

        resource_before = {pid: s.resource for pid, s in self.players.items()}

        # Pass 1: gather requests, so the pool sees total demand before granting any of it.
        requested: dict[str, float] = {}
        for pid, state in self.players.items():
            if not state.alive:
                continue
            action = actions.get(pid)
            if action is not None and action.type == ActionType.GATHER:
                requested[pid] = gather_yield(self.round, self.scenario)
        granted = self.pool.draw_and_regenerate(requested, self.round, self.scenario)
        for pid, amount in granted.items():
            self.players[pid].resource += amount

        # Reset last round's reciprocity signal before this round's shares land.
        for state in self.players.values():
            state.received_share_last_round = 0.0

        # Pass 2: everything else (share / hoard / move / skip / communicate), plus survival cost.
        log_rows: list[dict] = []
        for pid, state in self.players.items():
            if not state.alive:
                continue
            action = actions.get(pid) or Action(type=ActionType.SKIP)
            action.validate()

            target_agent: str | None = None
            message_sent: str | None = None

            if action.type == ActionType.SHARE:
                target_agent = action.target
                target_state = self.players.get(action.target)
                amount = action.amount or 0
                if target_state is not None and target_state.alive and state.resource >= amount:
                    state.resource -= amount
                    target_state.resource += amount
                    target_state.received_share_last_round += amount
                if action.message is not None:
                    message_sent = action.message.surface
            elif action.type == ActionType.COMMUNICATE:
                target_agent = action.target
                if action.message is not None:
                    message_sent = action.message.surface
            # HOARD, MOVE, SKIP and GATHER (already applied in pass 1) take no further effect here.
            # HOARD and MOVE are currently no-ops distinct only in label — see ACTIONS.md rows for
            # both; that's an open call for Phase C, not something to pre-empt here.

            state.resource -= SURVIVAL_COST
            state.alive = is_alive(state.resource)
            state.last_action = action.type
            state.last_action_target = target_agent

            log_rows.append(
                {
                    "agent_id": pid,
                    "round": self.round,
                    "scenario": self.scenario,
                    "action_type": action.type.value,
                    "target_agent": target_agent,
                    "message_sent": message_sent,
                    "resource_before": resource_before[pid],
                    "resource_after": state.resource,
                    "alive": state.alive,
                }
            )

        done = self.round >= self.total_rounds or all(not s.alive for s in self.players.values())
        if not done:
            self.round += 1
        return self._observations(), done, log_rows
