"""Canonical game constants — the single source both branches import.

Values here are adopted from Group 1's shipped `human_interface/app.py`, not from the original
roadmap draft. See INTEGRATION_ISSUES.md #5 for the reconciliation table and why the human app's
numbers win: participants will actually play those numbers, so the AI side conforms to them rather
than the reverse.

Do not redeclare any of these values elsewhere (that `# keep in sync` comment in app.py is exactly
the drift this module exists to prevent) — import from here instead.
"""

GRID_SIZE = 5

# 4 co-players (fixed policy, supplied by agents/coplayers.py — see PHASE_PLAN.md Phase B) + 1 focal
# player, who is human in one arm and an AI agent in the other. See INTEGRATION_ISSUES.md Blocker 1
# for why this replaced the original 4-independent-agents design.
NUM_PLAYERS = 5

TOTAL_ROUNDS = 10
DROUGHT_ROUND = 6

START_WATER = 5
SURVIVAL_COST = 2  # water consumed per round, regardless of action taken
GATHER_NORMAL = 3  # water gained by `gather` outside a drought round
GATHER_DROUGHT = 1  # water gained by `gather` during a drought round

# Scenario enum shared by the schema validator. "asymmetric" (unequal starting stock) is proposed
# in agents/PHASE_PLAN.md but not yet agreed with Group 1 — add it here only once it is.
SCENARIOS = ("calm", "drought", "repeated_trust")


def is_drought(round_num: int, scenario: str) -> bool:
    """Whether `round_num` is under drought conditions for `scenario`."""
    return scenario == "drought" and round_num == DROUGHT_ROUND


def gather_yield(round_num: int, scenario: str) -> int:
    """Water gained by a `gather` action this round."""
    return GATHER_DROUGHT if is_drought(round_num, scenario) else GATHER_NORMAL


def is_alive(resource: float) -> bool:
    """Survival rule, matching `human_interface/app.py`: alive at exactly 0 water.

    Evaluate this *after* subtracting SURVIVAL_COST for the round.
    """
    return resource >= 0
