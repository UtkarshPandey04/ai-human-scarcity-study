# ACTIONS.md — Canonical Action Space

Single source of truth for the action space, per `CLAUDE.md` and `Research_Roadmap_AI_Human_Scarcity_Study.md`.
Both `agents/` (Group 2, RL/LLM-driven) and `human_interface/` (Group 1, Streamlit buttons) must
expose exactly this set — the whole study depends on both tracks exercising the same action space.
`common/actions.py` is the importable version of this spec.

> **Status:** `gather`, `share`, `hoard`, `move`, `skip` are implemented in
> `human_interface/app.py`. `communicate` and the structured `Message` slot below are **proposed**,
> not yet built on either side — see `INTEGRATION_ISSUES.md` Blocker 2. This file is the spec to
> build against once the team agrees to it; don't treat it as already-shipped.

## Constants

All game constants (grid size, round count, survival cost, etc.) live in `common/config.py` — not
here, and not duplicated anywhere else.

## Actions

| Action | Arity | Precondition | Effect | `action_type` in log |
|---|---|---|---|---|
| `gather` | none | agent alive | `resource += gather_yield(round, scenario)` — see `common/config.py` | `gather` |
| `share(target, amount)` | `target`: player id · `amount`: int > 0 | agent alive, `resource >= amount` | `resource -= amount` on self, `resource += amount` on `target` | `share` |
| `hoard` | none | agent alive | **Open issue — see `INTEGRATION_ISSUES.md` #3.** No resource effect today, which makes it mechanically identical to `skip`. Either give it a real effect (e.g. protects stock from a shared-pool draw) or drop it and derive a hoarding index from gather-vs-share ratios instead. Decide before any real trials run. | `hoard` |
| `move(direction)` | `direction`: north / south / east / west | agent alive | Changes the agent's grid cell by one step. **Open issue — see `INTEGRATION_ISSUES.md` Blocker 3.** No grid exists today, so this is currently a no-op; the grid-or-no-grid decision affects the paper's spatial-embodiment framing, not just this row. | `move` |
| `skip` | none | agent alive | no effect | `skip` |
| `communicate(target, message)` | `target`: player id or `"all"` · `message`: a `Message` (below) | agent alive | no resource effect; message recorded in `meta.claim` and mirrored into `message_sent` | `communicate` |

Every round, regardless of action taken: `resource -= SURVIVAL_COST`. Survival is evaluated
**after** that deduction: `alive = (resource >= 0)` — see `common/config.py:is_alive`. An agent at
exactly 0 water is alive and can act next round.

## The `Message` slot

Attached to `share` or `communicate`. **Structured, not free text.** See
`INTEGRATION_ISSUES.md` Blocker 2 for the full rationale — the short version: a slotted claim
makes deception and promise-breaking machine-verifiable instead of requiring an LLM judge or
hand-coded interpretation, which is a methodological weakness in nearly every comparable paper
(see `paper/RELATED_WORK.md`).

| Field | Type | Notes |
|---|---|---|
| `kind` | `claim_stock` \| `promise_share` \| `request` \| `accuse` \| `none` | what kind of claim this is |
| `value` | int or null | the claimed number — e.g. claimed stock, or a promised share amount |
| `target` | player id or `"all"` | who the message is directed at |
| `surface` | string or null | optional free-text rendering, for the qualitative transcript pass (roadmap Phase 3 Step 4) |

Deception, once this lands, is computable rather than judged:
`deception = (kind == "claim_stock") and (value != true_stock)`.
Promise-breaking: promised at round *t*, not executed by round *t+1*.

In the human UI this is one dropdown (`kind`) + one number input (`value`) + the existing free-text
box (`surface`) — not a redesign of the game screen.

## Log encoding

Every action produces one row matching `LOGGING_SCHEMA.md`. `target_agent` and `message_sent` map
to `Message.target` and `Message.surface` respectively; the full structured message, once adopted,
lives in `meta.claim`. `common/schema.py` enforces this; treat it as authoritative over this
document for anything code-checked, and fix the drift if the two ever disagree.
