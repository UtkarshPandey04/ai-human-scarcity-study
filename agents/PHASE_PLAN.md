# Phase Plan — `group2-agents` (Simulation & AI Agents track)

**Owners:** Yashash & Saksham
**Scope:** `agents/`, `data/ai_logs/`, plus the two spec files the whole team depends on (`ACTIONS.md`, `data/LOGGING_SCHEMA.md`).
**Out of scope:** Streamlit app, consent/ethics, recruitment (that's `group1-human-study`).

> Branch naming warning: the roadmap calls this track "Group 1"; the branch is `group2-agents`.
> Go by the branch suffix (`-agents`). See CLAUDE.md.

---

## Guiding constraints

1. **The spec is the product.** Everything the other branch builds is downstream of `ACTIONS.md` and
   `LOGGING_SCHEMA.md`. Freeze both in Phase A. Any later change is a two-branch coordinated change.
2. **Every phase ends in a runnable artifact and a gate.** Don't advance on a gate you can't demo.
3. **Human data is the bottleneck, not AI data.** AI trials are cheap and re-runnable; human trials are
   not. Any design choice that makes the human session longer or more confusing is a bad choice —
   the AI side must bend to fit the human protocol, never the reverse.
4. **Budget discipline.** LLM calls are the only real cost. The reflex/deliberate split (Phase F) exists
   as much for cost as for science.

---

## Phase A — Contracts & scaffolding (Week 1)

**Goal:** freeze the two interfaces both branches code against, and make violations impossible to commit.

| File | What it is |
|---|---|
| `ACTIONS.md` (repo root) | Canonical action space. One table: action, arity, preconditions, effect, log encoding. |
| `data/LOGGING_SCHEMA.md` | Prose + JSON Schema for the log row. Currently empty — this phase fills it. |
| `common/schema.py` | The JSON Schema as code + `validate_row(row)` + `validate_trial(rows)`. |
| `common/actions.py` | `Action` enum / dataclasses. Single source both tracks import. |
| `requirements.txt` | Pin only what's actually used. Add as you go, not up front. |
| `Makefile` / `tasks.py` | `make smoke`, `make trials`, `make validate` — so nobody memorises commands. |

**Decisions to lock now (don't relitigate later):**

- **Grid:** 5×5, 4 agents, one resource (water). Partial observability: agent sees its own cell + the
  4-neighbourhood + a public "board" of every agent's *last public action* (not their true stock).
  Hidden stock is what makes deception possible — it's the whole engine of the paper.
- **Round budget:** 12 rounds. Long enough for reciprocity to form and a mid-game shock to bite;
  short enough that a human plays 3–4 scenarios inside a 20-minute session.
- **Message channel:** *structured*, not free text. See Phase C — this is the biggest methodological
  upgrade over the roadmap and it must be decided here.
- **Seeds:** every trial is `(scenario, severity, seed, arm)`. Same seed → identical world for AI and
  human. This is what makes the AI-vs-human comparison *matched* rather than merely parallel.

**Gate A:** `make validate` rejects a deliberately malformed row; `group1-human-study` can
`from common.schema import validate_row` and it passes on their first hand-written log row.

---

## Phase B — Environment core (Week 2)

**Files:** `agents/environment.py`, `agents/scenarios.py`, `agents/smoke_random.py`

- `ScarcityEnv` with `reset(seed) -> obs`, `step(actions: dict[agent_id, Action]) -> (obs, rewards, done, info)`.
- Resource dynamics: per-cell stock, logistic regeneration `r_{t+1} = r_t + g·r_t·(1 − r_t/K)`.
  Logistic (not linear) regen is what creates a genuine commons — over-harvest can push the pool past
  a point of no return, which is the phenomenon GovSim measures and the reason a tragedy exists at all.
- Consumption: each agent burns 1 unit/round. Stock 0 at end of round → `alive = false`, agent is out.
- **Scenario module** (`scenarios.py`), each a declarative dict, not a code branch:
  - `calm` — no shock, control condition.
  - `drought` — round 6, regeneration `g` cut by a severity factor.
  - `repeated_trust` — same 4 agents, 3 consecutive 12-round blocks with carry-over reputation.
  - `asymmetric` — agents start with unequal stock (2, 3, 5, 6). Cheap to add, and it's the condition
    where human fairness norms diverge hardest from LLM behaviour.
- Determinism: `env(seed=k)` replayed twice under identical actions must yield byte-identical logs.
  Write this as a test now; it will save you in Week 6.

**Gate B:** `python -m agents.smoke_random --scenario drought --seed 0` runs 12 rounds of uniform-random
actions, writes `data/ai_logs/…jsonl`, and `make validate` passes on it. Replay test green.

---

## Phase C — Action space + verifiable communication (Week 2–3)

**Files:** `agents/comms.py`, `ACTIONS.md` (finalised)

Actions: `gather`, `share(target, amount)`, `hoard`, `move(dir)`, `skip`, `communicate(target, message)`.

**The upgrade:** make `message` a *slotted claim*, not free text.

```python
Message = {
  "kind": "claim_stock" | "promise_share" | "request" | "accuse" | "none",
  "value": int | None,      # e.g. claimed stock, promised amount
  "target": "A2" | "all",
  "surface": "I only have 1 left, please spare some"   # rendered/free text, for qualitative pass
}
```

Why this matters more than anything else in the plan: **it makes deception ground-truth computable.**
`deception = (kind == "claim_stock") and (value != true_stock)`. `promise_break = promised share
at round t, did not execute at t+1`. Every prior LLM-society paper either hand-codes deception or uses
an LLM judge — both are contestable. Yours is arithmetic. Reviewers cannot argue with arithmetic.

Humans get the same slots as dropdowns + an optional free-text `surface` field; the LLM emits the same
JSON. Identical channel, identical parse path, zero interpretation gap.

**Gate C:** `ACTIONS.md` merged to `main`; the human-study branch has built its buttons from it without
asking a clarifying question.

---

## Phase D — RL reflex policy (Week 3–4)

**File:** `agents/rl_policy.py`

**⚠ Correct a trap in the roadmap:** Stable-Baselines3 PPO is **single-agent**. You cannot drop 4
agents into it. Two viable routes:

- **Recommended — parameter-shared IPPO via self-play.** Wrap the env so each agent's
  `(obs, action, reward)` is a separate sample into *one shared* PPO policy. Other agents act with a
  frozen snapshot of that same policy. This is standard, it's ~40 lines of wrapper, and it justifies
  itself in the paper as "homogeneous population, shared policy."
- Alternative: PettingZoo `ParallelEnv` + a MARL library. More correct, more setup cost. Only take this
  if IPPO visibly fails.

Train on `calm` **only**. Curriculum: the RL layer should learn *movement and harvest timing*, nothing
social. Freeze it before touching the LLM.

**Gate D:** shared PPO policy beats a random baseline on mean survival under `calm` by a clear margin
(target: ≥90% of agents alive at round 12 vs. random's baseline), across 20 held-out seeds. If the RL
agent can't survive with *no* scarcity shock, the environment is misspecified — stop and fix the env,
don't tune hyperparameters.

---

## Phase E — LLM reasoning layer (Week 4–5)

**Files:** `agents/llm_reasoning.py`, `agents/prompts/`, `agents/llm_client.py`

- **Provider abstraction first.** `llm_client.py` exposes `complete(messages, schema) -> dict` and is
  backed by whichever of OpenAI / Groq / Gemini / Ollama you have. Never let a provider SDK leak into
  `llm_reasoning.py` — you *will* switch providers when a free tier runs out mid-Week-6.
- **Constrained decoding / JSON mode**, plus a repair loop: parse → on failure, one retry with the
  validation error appended → on second failure, log `action_type: "skip"` and set
  `info.llm_parse_failure = true`. Never crash a trial, never silently substitute a random action —
  a parse failure is *data* and its rate goes in the paper.
- **Prompt = observation, verbatim.** The prompt must contain exactly the information the human sees on
  screen. No more (no hidden true stocks of others), no less. Write a single
  `render_observation(obs) -> str` used by both the prompt builder and, in text form, the Streamlit
  instructions. Any asymmetry here is a fatal confound.
- **Cache** on `hash(prompt)`. Deterministic scenarios will repeat prefixes heavily; this cuts cost a lot.
- **Cost meter:** log tokens + estimated cost per trial into `info`. You need this to plan Phase G.

**Gate E:** one 12-round `drought` trial runs end-to-end on LLM decisions, produces schema-valid logs,
and `llm_parse_failure` rate < 2%.

---

## Phase F — Hybrid arbitration (Week 5)

**File:** `agents/hybrid_agent.py`

The architecture claim of your paper: **reflex vs. deliberation**.

```
if decision_is_social(obs):     # another agent adjacent, or a pending promise, or stock < threshold
    action = llm_reasoning.decide(obs)
else:
    action = rl_policy.act(obs)
```

Log `info.decision_source ∈ {rl, llm}` on every row. This gives you a free, novel figure — *how often
does the agent deliberate, and does deliberation rate rise with scarcity?* — and it's the mechanism
that keeps LLM spend tractable.

Build the three ablation arms now, because Phase G runs them all:

| Arm | Movement/harvest | Social decisions |
|---|---|---|
| `rl_only` | RL | RL (share/hoard as raw actions) |
| `llm_only` | LLM | LLM |
| `hybrid` | RL | LLM |

**Gate F:** all three arms run one trial each without code changes — arm is a CLI flag.

---

## Phase G — Trial campaign (Week 6)

**File:** `agents/run_ai_trials.py`

Design the run as a grid, not a loop:

```
scenario   ∈ {calm, drought, repeated_trust, asymmetric}
severity   ∈ {0.0, 0.3, 0.5, 0.7, 0.9}      ← the scarcity dose–response sweep
arm        ∈ {rl_only, llm_only, hybrid}
model      ∈ {model_A, model_B, model_C}     ← at least one open-weight
seed       ∈ 0..N
```

Full grid is large — **budget it deliberately**. Suggested allocation:
- Full grid at `hybrid` + `model_A` (this is the arm that mirrors the human protocol) — 100 seeds/cell.
- Ablation arms and extra models only at the 4 scenarios × severity ∈ {0.0, 0.7} — 30 seeds/cell.

Engineering requirements, all of which will bite you if skipped:
- **Resumable.** Trial completion is a file on disk; re-running skips existing `(scenario,severity,arm,model,seed)`.
- **Parallel** across seeds with a worker pool + a rate limiter on the LLM client.
- **Manifest.** `data/ai_logs/manifest.json` records git SHA, model name+version, prompt file hash,
  env config, timestamp per trial. Without this your results are not reproducible and you will not be
  able to answer a reviewer asking "which model version?".
- **The human-matched subset must be flagged.** The seeds that humans will also play get
  `info.matched_seed = true`. Coordinate this list with `group1-human-study` *before* they recruit.

**Gate G:** ≥100 valid trials for each of the 4 scenarios in the primary arm; manifest complete; total
spend within budget.

---

## Phase H — Validation, freeze, handoff (Week 7)

- **Log QA script** (`agents/qa_logs.py`): schema pass rate, per-scenario row counts, resource
  conservation check (no water created or destroyed outside regeneration), no actions after death,
  no shares to dead agents, parse-failure rate, cost total.
- **Feature-extraction smoke test.** Run the joint `analysis/feature_extraction.py` against AI logs
  *early*, in Week 7 — not Week 8. If a metric can't be computed from your logs, you still have time
  to re-run trials. In Week 8 you don't.
- **Freeze `ai_logs_v1`**, tag the commit, write `data/ai_logs/README.md` describing the release.
- **Draft Methodology 4.1 (environment & scenarios) and 4.2 (agent architecture)** while the design is
  fresh in your head. Include the reflex/deliberation figure and the arm table.

**Gate H:** `group1-human-study` + the joint analysis crew can compute every metric in the roadmap's
Phase 3 Step 1 from your frozen logs, with no follow-up questions to you.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| SB3 can't do multi-agent as roadmap assumes | **High** | Phase D parameter-shared IPPO wrapper; decided up front |
| LLM free tier exhausted mid-campaign | High | Provider abstraction (Phase E) + Ollama fallback + cache + hybrid gating |
| Ethics approval slips → human trials late | High | AI track is independent until Week 8. Keep it that way. Don't couple your schedule to theirs |
| Human N too small for the classifier | Medium | Unit of analysis = **trial**, not participant. 30 people × 4 scenarios = 120 human trials. Plan power around that |
| Schema drift between branches | Medium | `common/schema.py` imported by both + CI validation on every commit |
| Deception unmeasurable from free-text logs | Medium | Solved structurally by Phase C slotted messages |
| Scope creep (10 scenarios, 5 models) | High | Cut list below |

**Cut list, in order, if you're behind:** extra models → `asymmetric` scenario → `repeated_trust` →
severity sweep down to 3 levels → ablation arms. **Never cut:** matched seeds, the manifest, or the
log QA script.

---

## Week-by-week

| Week | Phase | Ends with |
|---|---|---|
| 1 | A | Frozen `ACTIONS.md` + schema + validator both branches import |
| 2 | B, C | Random-agent trial writes valid logs; comms protocol final |
| 3 | C, D | PettingZoo/IPPO wrapper training |
| 4 | D, E | RL gate passed; LLM layer emitting valid JSON |
| 5 | E, F | Hybrid agent + 3 ablation arms runnable |
| 6 | G | Trial campaign complete, manifest written |
| 7 | H | `ai_logs_v1` frozen, Methodology 4.1–4.2 drafted |
