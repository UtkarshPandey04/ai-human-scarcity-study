# Group 2 — Agents Track: Status & Roadmap

**Branch:** `group2-agents` · **Owners:** Yashash & Saksham
**Scope:** `agents/`, `data/ai_logs/`, plus the shared contracts (`common/config.py`, `common/schema.py`,
`ACTIONS.md`, `LOGGING_SCHEMA.md`) that the human-study branch (`group1-human-study`) also depends on.

> **Naming note:** the original `Research_Roadmap_AI_Human_Scarcity_Study.md` calls this track "Group 1"
> (Simulation & AI Agents — Yashash & Saksham) and calls the human-study track "Group 2" (Sujal &
> Utkarsh). The actual git branches flip that: the agents work lives on **`group2-agents`**, the human
> study on `group1-human-study`. This document follows the branch name, since that's what the repo and
> the working `PHASE_PLAN.md` use — "group 2 agents" throughout this doc means the agents/environment/RL/LLM
> track, not the human-study track.

---

## 1. What this track is building

The study compares how AI-driven agents and human participants behave in the same resource-scarcity
"commons" game — a shared water pool, five players, a scripted drought, and an action space that
includes cooperation (`share`), self-interest (`hoard`), and deception (`communicate` with a claim that
may not match true stock). The agents track owns everything that produces the **AI half** of that
comparison: the simulated environment, the co-player policies the human side needs too, an RL reflex
policy, an LLM deliberation layer, a hybrid arbiter between the two, and the trial campaign that
generates `data/ai_logs/`.

---

## 2. Work completed so far, phase by phase

### Phase A — Contracts & scaffolding — ✅ done
Froze the interfaces both branches code against, so drift between the two halves becomes a merge
conflict instead of a silent bug.
- `common/config.py`: single source of every game constant (grid size, player count, rounds, survival
  cost, gather yields). Both branches import from here — no more locally-declared constants.
- `common/schema.py`: JSON Schema as code, plus `validate_row()` / `validate_trial()`, used by both the
  AI logger and the human app's `log_action()`.
- `common/actions.py`: `Action` dataclasses, including `communicate` and its structured message slot.
- `ACTIONS.md` / `LOGGING_SCHEMA.md`: canonical action space and logging contract, extended with a
  nested `meta` block (`severity`, `seed`, `arm`, `model`, `decision_latency_ms`, `claim`) so future
  fields never require renegotiating the top level.
- **Gate A passed:** `make validate` rejects malformed rows; the human app imports its constants from
  `common/config.py` instead of declaring its own.

### Phase B — Environment core + co-player policies — ✅ done
- `agents/environment.py`: `ScarcityEnv` with `reset(seed)` / `step(actions)`, mechanics matched to the
  human Streamlit app (same yields, survival cost, death rule) and verified with a parity test.
- Replaced the original flat per-action yield with a **shared, logistic-regenerating resource pool**
  (`r_{t+1} = r_t + g·r_t·(1 − r_t/K)`) — without this there's no real commons dilemma, since nothing can
  be collectively over-harvested past recovery. This was pushed back onto the human-study side as a
  required mirror.
- `agents/scenarios.py`: `calm`, `drought`, `repeated_trust` as declarative dicts (not code branches).
- `agents/coplayers.py`: the co-player policy pack (`cooperator`, `free_rider`, `tit_for_tat`, `random`)
  behind a frozen `act(obs) -> Action` interface — this is what makes **focal-player substitution**
  possible: every session has 5 players, 4 run a fixed co-player policy, and the 5th is swapped between
  a human and an AI agent under the same seed. That's what makes the AI-vs-human comparison *matched*
  rather than just parallel.
- **MSE-1 pilot-logs milestone hit:** ~20 random-agent trials run and summarized (`data/pilot_summary.md`)
  so the coursework EDA has real distributions instead of placeholders.
- **Gate B passed:** schema-valid logs from `smoke_random.py`, replay determinism test green, parity
  test against the human app green, `coplayers.py` merged and importable by the human-study side.

### Phase C — Action space & verifiable communication — done (folded into B/ongoing)
- Full six-action space finalized: `gather`, `share(target, amount)`, `hoard`, `move(dir)`, `skip`,
  `communicate(target, message)`.
- Messages are **slotted, not free text** (`{kind, value, target, surface}`), which is what makes
  deception measurable arithmetically (`claim_stock.value != true_stock`) instead of requiring an LLM
  judge or hand-coding — a deliberate design choice to avoid a weakness that gets attacked in review of
  comparable papers.
- Flagged and still open on the human-UI side: `communicate` didn't originally exist in `app.py`, and
  `hoard`/`skip` were identical no-ops there (would make "hoarding" measure self-labelling, not
  behavior) — tracked as cross-branch blockers, partly addressed already (see commit "Add human
  communication action and disclosure").

### Phase D — RL reflex policy — ✅ done, Gate D passed
- `agents/rl_policy.py`: Stable-Baselines3 PPO, implemented as **single-slot self-play** (one learner
  seat, the other four seats driven by the same live model via `set_self_play_policy`) rather than full
  multi-agent IPPO — a deliberate scope simplification, justified because Gate D's actual bar (beat
  random under `calm`) doesn't need the 5x sample efficiency of true IPPO.
- Learner action space restricted to `gather` / `hoard` / `skip` / `move` — no `share`, no
  `communicate` — so the RL layer only ever learns movement/harvest timing, never social behavior.
- **Real results, 20 held-out seeds:**

  | | Survival rate | Mean final resource |
  |---|---|---|
  | Trained policy | 100% | 16.45 |
  | Random baseline | 10% | -1.00 |

### Phase E — LLM reasoning layer — ✅ done, Gate E passed live
- `agents/llm_client.py`: provider abstraction (`complete(messages, schema=None)`) backed by Groq and
  Gemini.
- `agents/llm_reasoning.py`: `decide()` — parse the model's JSON, retry once with the validation error
  appended, fall back to `skip` with `meta.llm_parse_failure = true` on repeated failure. Never silently
  substitutes a random action.
- **Real live run** (`--scenario drought --seed 0 --provider groq`): 50/50 LLM calls succeeded (5
  players × 10 rounds), 0 parse failures, 38,597 prompt / 18,081 completion tokens. Real behavioral
  diversity showed up immediately in the drought round (hoarding, sharing, gathering all appeared across
  the five agents).
- Two real bugs found and fixed during this phase: a test that patched the wrong reference and was
  silently making live API calls on every `validate` run; both providers forcing JSON mode even with no
  schema (breaks Groq, which requires the literal word "json" in the prompt for JSON mode).
- Flagged, not yet resolved: the LLM prompt currently describes more of the world (shared pool level,
  others' last actions) than the human's Streamlit screen shows — needs the UI enriched or the prompt
  trimmed before this is used for anything beyond a structural smoke test, to avoid the two arms seeing
  different information.

### Phase F — Hybrid arbitration — ✅ done, Gate F passed
- `agents/hybrid_agent.py`: `is_social_decision(obs)` routes each round to the LLM or the RL policy;
  every log row records `meta.decision_source`. Trigger adapted for the no-grid environment: fires when
  a player is under resource pressure, it's a drought round, or another player shared with them last
  round — not on spatial adjacency (which doesn't exist here).
- **Real numbers, one script, three arms via a CLI flag** (`rl_only` / `llm_only` / `hybrid`):

  | Arm | Decisions | Notes |
  |---|---|---|
  | `rl_only` | 50/50 from RL | All 5 players survived all 10 rounds; $0 API cost |
  | `hybrid` | 43 RL / 7 LLM | ~14% real deliberation rate; 0 parse failures |
  | `llm_only` | 50/50 from LLM (Groq) | 0 parse failures, 0 rate-limited |

- **Real bug caught here, relevant to model choice going forward:** an early `llm_only` run against
  Gemini showed a 69% "parse failure" rate. Root cause traced to Gemini's free tier being capped at
  **20 requests/day/project/model** — this project's own testing had already burned most of that quota.
  Fixed properly rather than papered over: added a distinct `LLMRateLimitError` and a separate
  `meta.llm_rate_limited` flag, so a genuine model-quality metric (parse failure) is never conflated
  with an infrastructure limit (rate limiting) again. Any parse-failure-rate number computed for the
  paper must filter out rate-limited rows first.

### Phase G — Trial campaign — infrastructure ✅ built, full campaign **not yet run**
- `agents/run_ai_trials.py`: resumable (a finished trial is a file on disk), parallel across seeds with
  a worker pool and rate limiter, and writes `data/ai_logs/manifest.json` (git SHA, model name/version,
  prompt hash, env config, timestamp per trial).
- `severity` is now a real, continuous environment knob (`effective_growth = POOL_GROWTH_RATE *
  (1 - severity)`, applied every round, stacking with the scripted round-6 drought) rather than a logged
  placeholder — enables a proper dose–response sweep across scarcity levels instead of only an on/off
  drought flag.
- Budget shape implemented: full `scenario × severity` grid only on the primary arm (`hybrid`) and
  primary provider (`groq`) at 100 seeds/cell; cheaper ablation grid (`rl_only`, `llm_only`) at two
  severity levels, 30 seeds. Dry-run ceiling against the repo's 3 implemented scenarios: **1,860 trials,
  worst-case 84,000 LLM calls** (a ceiling — real `hybrid` deliberation rate was ~14% in Gate F).
- A tiny free `rl_only` batch (8 trials) was run end-to-end purely to prove the
  resumability/manifest/parallelism logic works, then deleted — not real campaign data.
- **What's still outstanding:** the actual budgeted campaign hasn't been spent (real money/quota
  decision); no agreed **matched-seed list** with the human-study side yet (the mechanism,
  `--matched-seeds`, exists but has nothing to point at); `repeated_trust` still has no scripted drought
  round, so `severity` is its only source of variation in the sweep.

### Phase H — Validation, freeze, handoff — not started
Planned: a log QA script (`agents/qa_logs.py` — schema pass rate, resource conservation, no
post-death actions, cost totals, run against both `ai_logs/` and `human_logs/`), a feature-extraction
smoke test, freezing `ai_logs_v1`, and drafting paper Methodology §4.1–4.2. None of this exists yet.

---

## 3. Snapshot: what's real vs. what's still a plan

| Phase | Status | Evidence |
|---|---|---|
| A — Contracts | ✅ Done | `common/config.py`, `common/schema.py` merged, Gate A passed |
| B — Env + co-players | ✅ Done | Gate B passed, pilot logs committed |
| C — Actions + comms | ✅ Done (folded into B) | Six-action space, slotted messages live |
| D — RL reflex policy | ✅ Done | Gate D: 100% vs 10% survival, real 20-seed eval |
| E — LLM reasoning | ✅ Done | Gate E: live Groq run, 0/50 parse failures |
| F — Hybrid arbitration | ✅ Done | Gate F: 3 arms, real bug found & fixed |
| G — Trial campaign | 🟡 Infra done, campaign not run | Dry-run only; real spend not yet authorized |
| H — Validation & freeze | ⬜ Not started | No `qa_logs.py`, no frozen `ai_logs_v1` yet |

The repo is currently ahead of the roadmap's original week numbering — Phases D–F, originally slated for
Weeks 3–5, are all complete, and Phase G's infrastructure (originally "Week 6") is also built. What
remains is **spending the actual trial budget** and **Phase H's validation/freeze/writing work**.

---

## 4. Prospective future work, by week

This assumes the current point in time is the start of the remaining work, using the track's own
week numbering (Weeks 6–8 per `PHASE_PLAN.md`, since Weeks 1–5 above are done).

### Week 6 — Run the trial campaign (Phase G completion)
- Get sign-off from whoever holds the API keys before spending real quota — this is a real-money,
  real-rate-limit action, not a dry run.
- Agree the **matched-seed list** with the human-study side *before* burning any seed that needs to
  pair with a human session — this is called out as a "never cut" item in the risk register.
- Run the primary grid (`hybrid` + `groq`, ~100 seeds/scenario) first since it mirrors the human
  protocol; run ablation arms (`rl_only`, `llm_only`) and any secondary model second, at the cheaper
  grid.
- Use `--limit N` to checkpoint spend in small increments rather than one long unattended run; verify
  `manifest.json` is populating correctly on the first batch before scaling up.
- Stay on Groq as the primary provider — Gemini's 20 req/day free-tier cap makes it unsafe at campaign
  scale until a quota increase is confirmed.
- **Exit criterion (Gate G):** ≥100 valid trials per scenario in the primary arm, manifest complete,
  spend within the agreed budget.

### Week 7 — Validation, freeze, handoff (Phase H)
- Write `agents/qa_logs.py`: schema pass rate, per-scenario row counts, resource conservation, no
  actions logged after death, no shares targeting dead players, parse-failure rate (with rate-limited
  rows filtered out), total cost. Run it against **both** `ai_logs/` and `human_logs/` — schema drift
  between the two branches is a shared failure, not just this track's.
- Run the feature-extraction smoke test now, not in Week 8 — if a Phase-3 metric (hoarding index,
  sharing rate, deception rate, alliance rate, survival rate, Gini coefficient) can't actually be
  computed from the logs, there's still time to re-run trials; a week later there isn't.
- Freeze `ai_logs_v1`, tag the commit, write `data/ai_logs/README.md` describing the frozen dataset.
- Draft paper Methodology §4.1 (simulation environment & scenarios) and §4.2 (AI agent architecture:
  RL + LLM hybrid) while the design decisions are still fresh — including the focal-player-substitution
  design, the reflex/deliberation split, and the arm comparison table.
- **Exit criterion (Gate H):** the joint-analysis crew can compute every roadmap Phase-3 metric from the
  frozen logs with no follow-up questions back to this track.

### Week 8 onward — Joint work (shared with the human-study track)
Once `ai_logs_v1` is frozen, this track's remaining responsibility shifts from building to supporting
the joint-analysis branch:
- Confirm the AI-side logs line up field-for-field with the human-side logs before feature extraction
  starts (this is what the Week 7 QA script is for).
- Be available to re-run or extend AI trials if the joint analysis surfaces a metric that needs more
  data (e.g., a scenario cell that's underpowered, or a model comparison reviewers will want).
- Contribute to the shared Methodology write-up (§4.1–4.2 already drafted in Week 7) and to
  Introduction/Discussion/Future-Work sections, which the roadmap explicitly calls out as needing
  whole-team perspective.

### Ongoing risk watch (not tied to a single week)
- **Blockers 1–3** in `INTEGRATION_ISSUES.md` must stay resolved on the human-UI side (focal-player
  substitution, shared-pool mechanics, communicate action) or the AI-vs-human comparison silently breaks
  even after this track's own work is "done."
- **`common/config.py` / `common/schema.py` drift** — any future change to either file is a coordinated
  two-branch change, not a unilateral one.
- **Cut list, in priority order, if the team falls behind:** extra models → `asymmetric` scenario →
  `repeated_trust` scenario → shrink the severity sweep to 3 levels → drop ablation arms.
  **Never cut:** matched seeds, the manifest, the log QA script, or `decision_latency_ms` logging on the
  human side.

---

*Compiled from `agents/PHASE_PLAN.md`, `INTEGRATION_ISSUES.md`, `Research_Roadmap_AI_Human_Scarcity_Study.md`,
and the `group2-agents` git history, as of the current state of the repository.*
