"""Declarative scenario configs. Add a new scenario here, not as a code branch in environment.py —
environment.py should never grow an `if scenario == "..."` beyond what `common/config.is_drought`
already needs.
"""

from __future__ import annotations

from dataclasses import dataclass

from common.config import TOTAL_ROUNDS


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    total_rounds: int
    description: str


SCENARIO_CONFIG: dict[str, ScenarioConfig] = {
    "calm": ScenarioConfig(
        name="calm",
        total_rounds=TOTAL_ROUNDS,
        description=(
            "Control condition. No scripted shock; the shared pool (environment.ResourcePool) is "
            "the only source of scarcity, and only if players over-harvest it."
        ),
    ),
    "drought": ScenarioConfig(
        name="drought",
        total_rounds=TOTAL_ROUNDS,
        description=(
            "Same as calm, except pool regeneration is cut during the drought round "
            "(common.config.DROUGHT_ROUND) — see environment.DROUGHT_GROWTH_MULTIPLIER. Individual "
            "gather yield also drops that round (common.config.GATHER_DROUGHT), matching "
            "human_interface/app.py exactly."
        ),
    ),
    "repeated_trust": ScenarioConfig(
        name="repeated_trust",
        total_rounds=TOTAL_ROUNDS * 3,
        description=(
            "Three consecutive 10-round blocks with the same players and no pool reset between "
            "them, so reciprocity (or its absence) in block 1 has visible consequences in "
            "blocks 2-3. First-pass implementation: no drought is scripted here yet, and there is "
            "no explicit 'block boundary' signal in Observation beyond `round`. Extend rather than "
            "branch if a future design needs one — this is intentionally the least-developed "
            "scenario; Gate B only requires calm/drought to be solid."
        ),
    ),
}
