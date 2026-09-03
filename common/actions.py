"""Canonical action space — the single source both `agents/` and `human_interface/` should import.

Six actions: gather, share, hoard, move, skip, communicate. `communicate` and the structured
`Message` slot are **proposed**, not yet implemented in `human_interface/app.py` — see
INTEGRATION_ISSUES.md Blocker 2. This module is nonetheless the target both sides build against
once that lands, so AI trials and human trials never drift.

See ACTIONS.md (repo root) for the prose spec this module implements.
"""

from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    GATHER = "gather"
    SHARE = "share"
    HOARD = "hoard"
    MOVE = "move"
    SKIP = "skip"
    COMMUNICATE = "communicate"


class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class MessageKind(str, Enum):
    """What kind of claim a message makes. See ACTIONS.md for the rationale: a slotted `value`
    turns deception into arithmetic (`CLAIM_STOCK` value != true stock) instead of something that
    needs an LLM judge or hand-coded interpretation.
    """

    CLAIM_STOCK = "claim_stock"
    PROMISE_SHARE = "promise_share"
    REQUEST = "request"
    ACCUSE = "accuse"
    NONE = "none"


@dataclass(frozen=True)
class Message:
    """A structured claim attached to `share` or `communicate` — not free text.

    `surface` carries an optional free-text rendering for the qualitative transcript pass
    (roadmap Phase 3 Step 4); `kind`/`value`/`target` are what analysis code actually reads.
    """

    kind: MessageKind = MessageKind.NONE
    value: int | None = None  # e.g. claimed stock, or a promised share amount
    target: str | None = None  # player id, or "all"
    surface: str | None = None


@dataclass(frozen=True)
class Action:
    type: ActionType
    target: str | None = None  # required for SHARE / COMMUNICATE
    amount: int | None = None  # required for SHARE
    direction: Direction | None = None  # required for MOVE
    message: Message | None = None  # optional, only meaningful with SHARE / COMMUNICATE

    def validate(self) -> None:
        """Raise ValueError if this action is structurally malformed.

        This checks shape only, not game-state preconditions (e.g. whether the agent actually
        has `amount` water to share) — those are the environment's job in Phase B.
        """
        if self.type == ActionType.SHARE:
            if self.target is None:
                raise ValueError("share requires a target")
            if self.amount is None or self.amount <= 0:
                raise ValueError("share requires a positive amount")
        elif self.type == ActionType.MOVE:
            if self.direction is None:
                raise ValueError("move requires a direction")
        elif self.type == ActionType.COMMUNICATE:
            if self.target is None:
                raise ValueError("communicate requires a target")
            if self.message is None:
                raise ValueError("communicate requires a message")
