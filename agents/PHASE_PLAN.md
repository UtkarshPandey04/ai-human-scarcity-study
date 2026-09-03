# Phase Plan — `group2-agents` (Simulation & AI Agents track)

**Owners:** Yashash & Saksham
**Scope:** `agents/`, `data/ai_logs/`, plus the shared contracts both branches depend on
(`common/config.py`, `common/schema.py`, `ACTIONS.md`, `LOGGING_SCHEMA.md`).
**Out of scope:** Streamlit app, consent/ethics, recruitment (that's `group1-human-study`).

> Branch naming warning: the roadmap calls this track "Group 1"; the branch is `group2-agents`.
> Go by the branch suffix (`-agents`). See CLAUDE.md.

> **Revised** after merging Group 1's human interface. Cross-branch mismatches and the fixes they
> need are in [`INTEGRATION_ISSUES.md`](../INTEGRATION_ISSUES.md) — read that first; three of its items
> are blockers that change what this plan can assume.

---

## Guiding constraints

1. **The spec is the product.** Everything the other branch builds is downstream of `common/config.py`,
   `common/schema.py` and `ACTIONS.md`. Freeze them in Phase A. Any later change is a coordinated
   two-branch change.
2. **Human data is the bottleneck, not AI data.** AI trials are cheap and re-runnable; human sessions
   are not. Any design choice that makes a human session longer or more confusing is a bad choice —
   the AI side bends to fit the human protocol, never the reverse. *Group 1's shipped constants are
   therefore canonical, not ours.*
3. **Every phase ends in a runnable artifact and a gate.** Don't advance on a gate you can't demo.
4. **Budget discipline.** LLM calls are the only real cost. The reflex/deliberate split (Phase F) exists
   as much for cost as for science.

---

## What changed after the merge

Group 1 shipped a working Streamlit flow (consent → instructions → game → debrief), a JSONL logger, a
populated `LOGGING_SCHEMA.md`, and a session-analysis module. Reading it against this plan surfaced
three things that change our work:

**We now owe Group 1 a deliverable we hadn't planned for: co-player policies.** The human app currently
has no other players — `share` sends water nowhere. The fix agreed in `INTEGRATION_ISSUES.md` is
**focal-player substitution**: every session has 5 players, 4 of them co-players on a fixed policy that
*we* supply, and the 5th is a human in one arm and an AI agent in the other. Same seed, same co-player
behaviour, only the focal player changes.

This is a better design than two independently-run societies — the comparison becomes strictly matched
— but it moves work forward into Phase B and makes the co-player interface a Week-2 deliverable rather
than a Week-6 one.

**Their game constants win, ours change.** Rounds 12 → **10**, agents 4 → **5**, survival cost 1 → **2**
per round. Full table in `INTEGRATION_ISSUES.md` §5. Not negotiable in our favour — their code is what
participants will actually play.

**MSE-1 needs pilot data sooner than Phase G delivers it.** The coursework deliverable wants EDA on real
numbers. Phase B now has an explicit pilot-logs milestone so we have distributions to plot before the
full campaign exists.

---

## Phase A — Contracts & scaffolding (Week 1)

**Goal:** freeze the interfaces both branches code against, and make violations impossible to commit.

| File | What it is |
|---|---|
| `common/config.py` | **Single source of every game constant.** Both branches import it. Replaces the `# keep in sync` comment in `app.py:21`, which will otherwise silently drift. |
| `common/schema.py` | JSON Schema as code + `validate_row(row)` + `validate_trial(rows)`. Group 1 calls this inside `log_action()`. |
| `common/actions.py` | `Action` dataclasses, including `communicate` and the structured message slot. |
| `ACTIONS.md` (root) | Canonical action space: action, arity, preconditions, effect, log encoding. |
| `LOGGING_SCHEMA.md` (root) | Extend Group 1's file with the `meta` block. Delete the empty `data/LOGGING_SCHEMA.md`. |
| `requirements.txt` | Pin only what's actually used. Add as you go. |
| `Makefile` | `make smoke`, `make pilot`, `make trials`, `make validate`. |

**Constants — adopted from Group 1, now canonical:**

```python
GRID_SIZE      = 5
NUM_PLAYERS    = 5      # 4 co-players + 1 focal player
TOTAL_ROUNDS   = 10
DROUGHT_ROUND  = 6
START_WATER    = 5
SURVIVAL_COST  = 2      # per round
GATHER_NORMAL  = 3
GATHER_DROUGHT = 1
# alive == (resource >= 0); an agent at exactly 0 can still act
```

**Schema extension — the `meta` block.** Nested, so the top level never needs renegotiating again:
`severity`, `seed`, `arm`, `model`, `decision_latency_ms`, `claim`. Rationale and the exact shape are in
`INTEGRATION_ISSUES.md` §6. Push Group 1 hard on `decision_latency_ms` — it's one Streamlit timer, and
after recruitment starts it can never be recovered.

**Still to lock in Phase A:**

- **Partial observability.** An agent sees its own stock, its cell, and a public board of every player's
  *last public action* — never another player's true stock. Hidden stock is what makes deception
  possible; it is the engine of the whole paper.
- **Seeds.** Every trial is `(scenario, severity, seed, arm)`. Same seed → identical world and identical
  co-player behaviour across the human and AI arms. This is what makes the comparison *matched* rather
  than merely parallel.
- **What co-players are said to be.** Whatever Group 1's consent text tells participants about the other
  players, our LLM prompt must say the same thing. See Blocker 1.

**Gate A:** `make validate` rejects a deliberately malformed row; Group 1 imports `validate_row` inside
`log_action()` and their existing logs still pass; `app.py` imports its constants from `common/config.py`
instead of declaring them.

---

## Phase B — Environment core + co-player policies (Week 2)

**Files:** `agents/environment.py`, `agents/scenarios.py`, `agents/coplayers.py`, `agents/smoke_random.py`

- `ScarcityEnv` with `reset(seed) -> obs`, `step(actions: dict[player_id, Action]) -> (obs, rewards, done, info)`.
- **Mechanics must match `app.py` exactly** — same gather yields, same survival cost, same death rule.
  Where they differ, the human app wins and we change. Write a test that asserts a single-player episode
  in our env reproduces the human app's resource trajectory for a fixed action sequence.
- **Resource dynamics.** Group 1's current model is a flat per-action yield with no shared pool. For a
  commons to exist at all there has to be a pool that players can collectively exhaust — logistic
  regeneration, `r_{t+1} = r_t + g·r_t·(1 − r_t/K)`, so over-harvest can push it past recovery. That
  irreversibility is the phenomenon GovSim measures and the reason a tragedy exists. **This is a change
  Group 1 has to mirror**, so raise it early; it's the one place where our side should push back on
  theirs, because without it there is no commons dilemma to study.
- **Scenarios** as declarative dicts, not code branches: `calm` (control), `drought` (round 6),
  `repeated_trust` (three blocks, carried reputation), and `asymmetric` (unequal starts) if Group 1
  adds it to the scenario enum.
- **Co-player policy pack** (`coplayers.py`) — the new deliverable for Group 1. A frozen interface,
  `act(obs) -> Action`, with a few named policies (`cooperator`, `free_rider`, `tit_for_tat`,
  `random`). Ship this in Week 2 even if the policies are trivial; Group 1 is blocked without it and
  they should not be writing agent behaviour themselves.
- **Determinism.** Same seed replayed under identical actions must produce byte-identical logs. Write
  the test now; it will save you in Week 6.

**Milestone — MSE-1 pilot logs.** Before the phase ends, run ~20 random-agent trials and commit the
derived summary (not the raw logs) so the coursework EDA has real distributions: action counts,
resource-over-rounds, survival rate by scenario.

**Gate B:** `python -m agents.smoke_random --scenario drought --seed 0` writes schema-valid logs; replay
test green; parity test against `app.py` green; `coplayers.py` merged to `main` and importable by
Group 1.

---

## Phase C — Action space & verifiable communication (Weeks 2–3)

**Files:** `agents/comms.py`, `ACTIONS.md` (finalised)

Actions: `gather`, `share(target, amount)`, `hoard`, `move(dir)`, `skip`, `communicate(target, message)`.

Two things here are now blocking issues on Group 1's side rather than upgrades on ours:

- **`communicate` doesn't exist in the human app** (`app.py:27`), though the schema lists it and the
  instructions promise it. Without it a participant can never make a standalone claim, so deception
  cannot occur, let alone be measured.
- **Messages must be slotted, not free text** — `{kind, value, target, surface}`. This makes deception
  arithmetic: `claim_stock.value != true_stock`. Every comparable paper hand-codes deception or uses an
  LLM judge; both get attacked in review. Ours can't be. The free-text `surface` field survives for the
  qualitative transcript pass.

Also unresolved from the merge: **`hoard` and `skip` are currently identical no-ops** in the human app,
so the hoarding index would measure self-labelling rather than behaviour. Either `hoard` gets a real
mechanical effect or hoarding gets derived from gather-vs-share ratios. Decide before trials.

**Gate C:** `ACTIONS.md` merged to `main`; Group 1's UI exposes all six actions and the message slots;
a human-arm log row and an AI-arm log row for the same action are byte-identical apart from `source`
and `meta`.

---

## Phase D — RL reflex policy (Weeks 3–4)

**File:** `agents/rl_policy.py`

**⚠ Trap in the roadmap:** Stable-Baselines3 PPO is **single-agent**. You cannot drop five agents into
it. Two routes:

- **Recommended — parameter-shared IPPO via self-play.** Each agent's `(obs, action, reward)` is a
  separate sample into one shared PPO policy; other agents act with a frozen snapshot of it. ~40 lines
  of wrapper, and it justifies itself in the paper as a homogeneous shared-policy population.
- Alternative: PettingZoo `ParallelEnv` + a MARL library. More correct, more setup. Take it only if
  IPPO visibly fails.

Train on `calm` only. The RL layer learns movement and harvest timing — nothing social. Freeze it before
the LLM enters.

**Gate D:** shared policy beats random on mean survival under `calm` across 20 held-out seeds. If the RL
agent can't survive with no scarcity shock at all, the environment is misspecified — stop and fix the
environment, don't tune hyperparameters.

---

## Phase E — LLM reasoning layer (Weeks 4–5)

**Files:** `agents/llm_reasoning.py`, `agents/llm_client.py`, `agents/prompts/`

- **Provider abstraction first.** One `complete(messages, schema) -> dict` entry point. Never let a
  vendor SDK leak into the reasoning module — you *will* switch providers when a free tier runs out
  mid-Week-6.
- **Parse failures are data, not crashes.** Parse → retry once with the validation error appended → fall
  back to `skip` with `meta.llm_parse_failure = true`. Never silently substitute a random action; the
  failure rate goes in the paper.
- **The prompt is the human's screen, verbatim.** One `render_observation()` feeds both the prompt
  builder and Group 1's instructions text. Any asymmetry is a fatal confound — it is exactly the mistake
  that sank the comparison in arXiv:2505.17937. This now includes **what the agent is told about its
  co-players**, which must match the consent text word for word.
- Cache on prompt hash; log tokens and cost per trial into `meta`.

**Gate E:** one full `drought` trial runs end-to-end on LLM decisions, logs validate, parse-failure rate
under 2%.

---

## Phase F — Hybrid arbitration (Week 5)

**File:** `agents/hybrid_agent.py`

The architectural claim of the paper: reflex versus deliberation. Route social decisions — another
player adjacent, a pending promise, stock below threshold — to the LLM; everything else to the RL
policy. Log `meta.decision_source` on every row.

That field buys a free figure: *how often does the agent deliberate, and does deliberation rate climb
with scarcity?* — and with Group 1 logging `decision_latency_ms`, it goes on the same axis as human
deliberation time.

Build the three ablation arms now, because Phase G runs all of them: `rl_only`, `llm_only`, `hybrid`.

**Gate F:** all three arms run a trial each with no code change — the arm is a CLI flag.

---

## Phase G — Trial campaign (Week 6)

**File:** `agents/run_ai_trials.py`

Design the run as a grid, not a loop:

```
scenario   ∈ {calm, drought, repeated_trust, asymmetric?}
severity   ∈ {0.0, 0.3, 0.5, 0.7, 0.9}      ← the scarcity dose–response sweep
arm        ∈ {rl_only, llm_only, hybrid}
model      ∈ {model_A, model_B, model_C}     ← at least one open-weight
seed       ∈ 0..N
```

Budget it deliberately: full grid on `hybrid` + `model_A` (the arm mirroring the human protocol) at 100
seeds per cell; ablation arms and extra models only at 4 scenarios × severity ∈ {0.0, 0.7}, 30 seeds.

- **Resumable.** Trial completion is a file on disk; a re-run skips what exists.
- **Parallel** across seeds with a worker pool and a rate limiter on the LLM client.
- **Manifest.** `data/ai_logs/manifest.json` records git SHA, model name and version, prompt file hash,
  env config, timestamp per trial. Without it you cannot answer a reviewer asking which model version
  produced a result.
- **Matched seeds.** Every seed a human will also play gets `meta.matched_seed = true`, with identical
  co-player policies. Agree that seed list with Group 1 *before* they recruit.

**Gate G:** ≥100 valid trials per scenario in the primary arm; manifest complete; spend within budget.

---

## Phase H — Validation, freeze, handoff (Week 7)

- **Log QA script** (`agents/qa_logs.py`): schema pass rate, per-scenario row counts, resource
  conservation, no actions after death, no shares to dead players, parse-failure rate, cost total.
  Run it against **both** `ai_logs/` and `human_logs/` — schema drift is a two-branch failure.
- **Feature-extraction smoke test in Week 7, not Week 8.** If a metric can't be computed from the logs
  you still have time to re-run trials. In Week 8 you don't.
- **Freeze `ai_logs_v1`**, tag the commit, write `data/ai_logs/README.md`.
- **Draft Methodology 4.1–4.2** while the design is fresh, including the focal-player substitution
  design, the reflex/deliberation figure, and the arm table.

**Gate H:** the analysis crew computes every roadmap Phase 3 metric from the frozen logs with no
follow-up questions.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Blockers 1–3 not resolved before recruitment | **High** | `INTEGRATION_ISSUES.md` on the next meeting agenda; ethics disclosure decision is on the critical path |
| Constants drift between the two codebases | **High** | `common/config.py` imported by both; the `# keep in sync` comment deleted, not trusted |
| SB3 can't do multi-agent as roadmap assumes | High | Phase D parameter-shared IPPO wrapper, decided up front |
| LLM free tier exhausted mid-campaign | High | Provider abstraction, local fallback, prompt cache, hybrid gating |
| Ethics approval slips → human trials late | High | This track is independent until Week 8 — keep it that way |
| Scope creep (10 scenarios, 5 models) | High | Cut list below |
| Co-player policies late → Group 1 blocked | Medium | Ship `coplayers.py` in Week 2 even if the policies are trivial |
| Human N too small for the classifier | Medium | Unit of analysis is the **trial**, not the participant — 30 people × 4 scenarios = 120 trials |
| Deception unmeasurable from free-text logs | Medium | Solved structurally by Phase C slotted messages — *if Group 1 ships them* |
| MSE-1 EDA has no real data | Medium | Phase B pilot-logs milestone |

**Cut list, in order, if you're behind:** extra models → `asymmetric` → `repeated_trust` → severity sweep
down to 3 levels → ablation arms → the grid (Blocker 3 option b).
**Never cut:** matched seeds, the manifest, the log QA script, or `decision_latency_ms`.

---

## Week-by-week

| Week | Phase | Ends with |
|---|---|---|
| 1 | A | `common/config.py` + `common/schema.py` imported by both branches; `meta` block agreed |
| 2 | B, C | Env matches `app.py` mechanics; `coplayers.py` shipped to Group 1; **MSE-1 pilot logs** |
| 3 | C, D | Six-action space live on both sides; IPPO wrapper training |
| 4 | D, E | RL gate passed; LLM layer emitting valid JSON |
| 5 | E, F | Hybrid agent + 3 ablation arms runnable |
| 6 | G | Trial campaign complete, manifest written |
| 7 | H | `ai_logs_v1` frozen, Methodology 4.1–4.2 drafted |
