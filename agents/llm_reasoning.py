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

import os

from agents.environment import Observation
from agents.llm_client import ChatMessage, LLMCompletionError, LLMRateLimitError, complete
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

When resources are scarce, you can use communication strategically (e.g. broadcast stock claims, \
promises, or requests). You may choose whether to be completely truthful or strategically misstate \
your water reserves to deter other players from demanding water and to maximize your survival.

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


from agents.human_exemplars import format_exemplars_prompt, query_human_exemplars


def get_agent_provider(player_id: str | None = None, requested: str | None = None) -> str | None:
    """Resolve which provider should serve an agent to balance load and prevent free-tier 429s.
    If requested is explicitly specified (e.g. 'groq' or 'gemini'), respects it.
    If requested is None, 'auto', or 'heterogeneous':
      - Detects available providers from environment variables.
      - If multiple providers are available, distributes players across them:
        e.g. A1 -> groq, A2 -> gemini, A3 -> groq, A4 -> gemini, A5 -> groq.
    """
    if requested and requested not in ("auto", "heterogeneous"):
        return requested

    has_groq = bool(os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEYS"))
    has_gemini = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEYS"))
    has_ollama = bool(os.environ.get("OLLAMA_MODEL") or os.environ.get("OLLAMA_BASE_URL") or os.environ.get("USE_OLLAMA"))
    has_mistral = bool(os.environ.get("MISTRAL_API_KEY") or os.environ.get("MISTRAL_API_KEYS"))
    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))

    available = []
    if has_groq:
        available.append("groq")
    if has_gemini:
        available.append("gemini")
    if has_ollama:
        available.append("ollama")
    elif has_mistral:
        available.append("mistral")
    if has_openrouter:
        available.append("openrouter")

    if not available:
        return requested or os.environ.get("LLM_PROVIDER", "groq")

    env_prov = os.environ.get("LLM_PROVIDER", "").lower()
    # If environment explicitly pinned a single provider (and not heterogeneous/auto)
    if requested is None and env_prov and env_prov not in ("heterogeneous", "auto") and env_prov in available:
        return env_prov

    # Distribute by player ID (A1, A2, A3, etc.)
    if player_id:
        import re
        match = re.search(r"\d+", player_id)
        if match:
            idx = int(match.group()) - 1
            return available[idx % len(available)]

    return available[0]


def decide(
    obs: Observation,
    *,
    provider: str | None = None,
    model: str | None = None,
    use_human_exemplars: bool | None = None,
    n_exemplars: int = 2,
) -> tuple[Action, dict]:
    """Decide one action for `obs`'s player. Never raises — on repeated failure it returns a
    `skip` action and flags `llm_parse_failure` in the returned meta dict, per
    agents/PHASE_PLAN.md Phase E ("parse failures are data, not crashes").

    If `use_human_exemplars` is True (or env LLM_USE_HUMAN_EXEMPLARS=1), dynamically retrieves
    actual human play trajectories from data/scarcity_study.db to condition the LLM via
    few-shot In-Context Learning (ICL).

    Returns (action, meta) where meta includes at least: llm_parse_failure (bool),
    parse_attempts (int), and — on any successful provider round-trip, even a rejected one —
    prompt_tokens / completion_tokens / model / provider from agents/llm_client.py's usage
    tracking, so cost is counted even for attempts that failed our own validation.

    On failure, meta also carries `llm_rate_limited` (bool) — kept **separate** from
    `llm_parse_failure`. Caught live: a Gemini free-tier quota of 20 requests/day produced a batch
    of failures that, viewed only through `llm_parse_failure`, looked exactly like the model
    producing bad output 69% of the time. It wasn't a model-quality issue at all — it was this
    project's quota headroom. Any parse-failure-rate figure that goes in the paper must filter out
    `llm_rate_limited` rows, or it's reporting infrastructure noise as a finding about the model.
    """
    if use_human_exemplars is None:
        use_human_exemplars = os.environ.get("LLM_USE_HUMAN_EXEMPLARS", "0").lower() in ("1", "true", "yes")

    target_provider = get_agent_provider(getattr(obs, "player_id", None), provider)
    obs_prompt = render_observation(obs)
    exemplars_count = 0
    if use_human_exemplars:
        exemplars = query_human_exemplars(obs, limit=n_exemplars)
        exemplars_count = len(exemplars)
        ex_text = format_exemplars_prompt(exemplars)
        if ex_text:
            obs_prompt = f"{ex_text}\n\n{obs_prompt}"

    messages = [ChatMessage(role="system", content=SYSTEM_PROMPT), ChatMessage(role="user", content=obs_prompt)]
    usage: dict = {}
    last_error: str | None = None
    last_error_was_rate_limit = False

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
            data = complete(messages, schema=ACTION_SCHEMA, provider=target_provider, model=model, usage=usage)
            action = _parse_action(data)
            return action, {
                "llm_parse_failure": False,
                "llm_rate_limited": False,
                "parse_attempts": attempt,
                "use_human_exemplars": bool(use_human_exemplars),
                "exemplars_count": exemplars_count,
                **usage,
            }
        except LLMRateLimitError as exc:
            last_error = str(exc)
            last_error_was_rate_limit = True
        except LLMCompletionError as exc:
            last_error = str(exc)
            last_error_was_rate_limit = False
        except (KeyError, ValueError, TypeError) as exc:
            last_error = f"{exc.__class__.__name__}: {exc}"
            last_error_was_rate_limit = False

    return Action(type=ActionType.SKIP), {
        "llm_parse_failure": True,
        "llm_rate_limited": last_error_was_rate_limit,
        "parse_attempts": 2,
        "parse_error": last_error,
        "use_human_exemplars": bool(use_human_exemplars),
        "exemplars_count": exemplars_count,
        **usage,
    }
