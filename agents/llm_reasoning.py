"""Phase E — the LLM reasoning layer. Given one player's Observation, decides a full Action
(any of the six — gather/share/hoard/move/skip/communicate; Phase F is what restricts this to
"social" decisions only when running hybrid, not this file). See agents/PHASE_PLAN.md Phase E.

## ⚠ Known asymmetry — read before trusting Gate E's numbers for anything beyond "does it run"

"The prompt is the human's screen, verbatim" is the core methodological requirement here (see
module-level warning below and PHASE_PLAN.md Phase E) — any gap between what the LLM is told and
what a human participant actually sees on screen is a confound, not a detail. Right now there IS a
gap: `render_observation()` below describes the shared pool's stock level and other players' last
public actions, because that's what a real commons game needs for a hoard/share decision to mean
anything. `human_interface/app.py`'s game screen does not display either of those yet — it only
shows the participant's own water and the round number. This isn't a Phase E bug; it's Phase E
correctly implementing the environment from agents/environment.py while the human UI hasn't caught
up. **Before this prompt is used for anything beyond a structural Gate E smoke test, either enrich
app.py's game screen to show pool level + other players' last actions, or strip those fields from
this prompt to match.** Don't let this drift silently — it is exactly the mistake that undermined
the human/AI comparison in arXiv:2505.17937 (see paper/RELATED_WORK.md).

Co-player disclosure text below is copied to match `human_interface/app.py`'s consent and
instructions screens (`consent_screen()` / `instructions_screen()`) as of the "Add human
communication action and disclosure" commit. If that wording changes on either side, update both —
grep for "computer-controlled co-players" to find every copy.
"""

from __future__ import annotations

from agents.environment import Observation
from agents.llm_client import ChatMessage, LLMCompletionError, complete
from common.actions import Action, ActionType, Direction, Message, MessageKind
from common.config import NUM_PLAYERS

# Matches human_interface/app.py's consent_screen() / instructions_screen() wording — see the
# module docstring above. Keep these in sync by hand; there's no shared source file yet (that
# would mean Group 1 importing from agents/, which the team layout doesn't do).
CO_PLAYER_DISCLOSURE = (
    f"You are one of {NUM_PLAYERS} players on a small island. The other players are "
    "computer-controlled co-players, not other human participants."
)

SYSTEM_PROMPT = f"""You are a player in a resource-scarcity survival game. {CO_PLAYER_DISCLOSURE}

Each round you need 2 units of water to survive. Water comes from a shared pool that all players \
draw from — if everyone over-harvests it, it can run dry for everyone. You may gather water, share \
some of your own water with another player, hoard (take no action), move (has no effect in this \
version of the game), skip your turn, or communicate a message to another player.

There are no right or wrong answers. Decide as you actually would in this situation, given your \
own goal of surviving as many rounds as possible."""

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {
            "type": "string",
            "enum": ["gather", "share", "hoard", "move", "skip", "communicate"],
        },
        "target": {
            "type": ["string", "null"],
            "description": "player id to target — required for share/communicate, else null",
        },
        "amount": {
            "type": ["integer", "null"],
            "description": "positive integer — required for share, else null",
        },
        "direction": {
            "type": ["string", "null"],
            "enum": ["north", "south", "east", "west", None],
            "description": "required for move, else null (has no game effect currently)",
        },
        "message": {
            "type": ["object", "null"],
            "description": "optional, only meaningful with share/communicate",
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": ["claim_stock", "promise_share", "request", "accuse", "none"],
                },
                "value": {"type": ["integer", "null"]},
                "target": {"type": ["string", "null"]},
                "surface": {"type": ["string", "null"], "description": "free-text wording"},
            },
        },
    },
    "required": ["action_type"],
}


def render_observation(obs: Observation) -> str:
    """The dynamic, per-round part of the prompt — what this player currently sees. See the
    module-level warning: this must stay aligned with what human_interface/app.py's game screen
    actually shows, not just with what agents/environment.py can compute.
    """
    lines = [
        f"Round {obs.round} of {obs.total_rounds}.",
        f"Your water: {obs.own_resource:.1f}.",
    ]
    if obs.is_drought:
        lines.append("⚠ This is a drought round — water is especially scarce.")
    if obs.pool_capacity:
        lines.append(f"Shared water pool: {obs.pool_stock:.1f} / {obs.pool_capacity:.0f}.")
    if obs.received_share_last_round > 0:
        lines.append(f"Another player shared {obs.received_share_last_round:.1f} water with you last round.")

    alive_others = [o for o in obs.others if o.alive]
    if alive_others:
        lines.append("Other players still in the game:")
        for other in alive_others:
            last = f"{other.last_action.value}" if other.last_action else "no action yet"
            if other.last_action_target:
                last += f" (targeting {other.last_action_target})"
            lines.append(f"  - {other.player_id}: last action was {last}")
    else:
        lines.append("No other players remain.")

    lines.append(
        "\nDecide your action. Respond only with the JSON object described in the schema — "
        "no other text."
    )
    return "\n".join(lines)


def _parse_action(data: dict) -> Action:
    action_type = ActionType(data["action_type"])  # raises ValueError on an invalid enum value

    direction = None
    if data.get("direction"):
        direction = Direction(data["direction"])

    message = None
    raw_message = data.get("message")
    if raw_message:
        message = Message(
            kind=MessageKind(raw_message.get("kind", "none")),
            value=raw_message.get("value"),
            target=raw_message.get("target"),
            surface=raw_message.get("surface"),
        )

    action = Action(
        type=action_type,
        target=data.get("target"),
        amount=data.get("amount"),
        direction=direction,
        message=message,
    )
    action.validate()  # raises ValueError, e.g. "share requires a target"
    return action


def decide(obs: Observation, *, provider: str | None = None, model: str | None = None) -> tuple[Action, dict]:
    """Decide one action for `obs`'s player. Never raises — on repeated failure it returns a
    `skip` action and flags `llm_parse_failure` in the returned meta dict, per
    agents/PHASE_PLAN.md Phase E ("parse failures are data, not crashes").

    Returns (action, meta) where meta includes at least: llm_parse_failure (bool),
    parse_attempts (int), and — on any successful provider round-trip, even a rejected one —
    prompt_tokens / completion_tokens / model / provider from agents/llm_client.py's usage
    tracking, so cost is counted even for attempts that failed our own validation.
    """
    messages = [ChatMessage(role="system", content=SYSTEM_PROMPT), ChatMessage(role="user", content=render_observation(obs))]
    usage: dict = {}
    last_error: str | None = None

    for attempt in (1, 2):
        if last_error is not None:
            messages = [
                *messages,
                ChatMessage(
                    role="user",
                    content=(
                        f"Your previous response was invalid: {last_error}\n"
                        "Respond again with corrected JSON matching the required schema."
                    ),
                ),
            ]
        try:
            data = complete(messages, schema=ACTION_SCHEMA, provider=provider, model=model, usage=usage)
            action = _parse_action(data)
            return action, {"llm_parse_failure": False, "parse_attempts": attempt, **usage}
        except LLMCompletionError as exc:
            last_error = str(exc)
        except (KeyError, ValueError, TypeError) as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"

    return Action(type=ActionType.SKIP), {
        "llm_parse_failure": True,
        "parse_attempts": 2,
        "parse_error": last_error,
        **usage,
    }
