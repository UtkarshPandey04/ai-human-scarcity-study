# 4. Methodology — §4.1 Simulation Environment, §4.2 AI Agent Architecture

*Draft by the agents track (`group2-agents`). Every number below is read from the code at the commit
this file was added in; if a constant changes, change it here too. Sections 4.3+ (human study,
analysis) belong to the human-study track and the joint-analysis branch.*

---

## 4.1 Simulation environment and scenarios

### 4.1.1 The commons game

Each trial is a repeated commons game among **five players** (`common/config.py: NUM_PLAYERS`). Every
player starts with **5 units of water** and pays a **survival cost of 2 units per round** regardless
of what they do; a player whose stock falls to zero or below is dead for the rest of the trial and
takes no further actions. A standard trial lasts **10 rounds**.

Water enters the economy only through a **shared, logistically regenerating pool** (`agents/
environment.py: ResourcePool`), capacity *K* = 100 and intrinsic growth rate *g* = 0.4. Each round:

1. Every player who chooses `gather` requests a fixed yield — **3 units** normally, **1 unit** in a
   drought round. If total demand exceeds current stock, every request is scaled down by the same
   proportion, so no player is arbitrarily prioritised.
2. The pool regenerates by *r*<sub>t+1</sub> = *r*<sub>t</sub> + *g′*·*r*<sub>t</sub>·(1 − *r*<sub>t</sub>/*K*),
   where *g′* = *g*·(1 − *s*) for the trial's scarcity severity *s* ∈ [0, 1], further multiplied by
   0.3 in a scripted drought round.
3. Transfers (`share`) are applied between living players.
4. Every living player pays the survival cost; death is evaluated on the post-transfer stock.

Steps 3 and 4 are separate passes over all players, so the outcome of a round does not depend on
the order in which players are processed — a share always lands before its recipient's survival
check. (An earlier implementation interleaved them per player; the resulting order dependence was
caught by the log QA invariants, see §4.2.6, and all logs used in this paper were produced after the
fix.)

Logistic regeneration is what makes this a genuine commons dilemma: because growth is proportional
to remaining stock, a pool harvested below roughly *K*/2 recovers progressively slower, and one
harvested to zero never recovers. Individually rational over-harvesting can therefore exhaust the
resource for everyone — a fixed per-action yield, as in the original design, would not have this
property.

### 4.1.2 Action space

All players — human or AI — choose from the same six actions (`ACTIONS.md`, `common/actions.py`):

| Action | Effect |
|---|---|
| `gather` | Request water from the shared pool (step 1 above) |
| `share(target, amount)` | Transfer `amount` of one's own water to a living player |
| `hoard` | No resource effect; a deliberate, labelled choice to keep one's stock |
| `move(direction)` | No resource effect in this version (no spatial grid; retained for schema parity) |
| `skip` | No resource effect |
| `communicate(target, message)` | Send a structured message (below) |

`share` may also carry a message. Messages are **slotted, not free text**: each has a `kind`
(`claim_stock`, `promise_share`, `request`, `accuse`, `none`), an optional numeric `value`, a
`target`, and a human-readable `surface` string. This makes deception arithmetically measurable —
a `claim_stock` message whose `value` differs from the sender's true stock at that moment is a
false claim — without an LLM judge or manual coding of free text.

### 4.1.3 Focal-player substitution

Every trial has five seats. Four are filled by fixed **co-player policies** (`agents/coplayers.py`);
the fifth, the **focal player**, is either a human participant or an AI agent. Running human and AI
trials **on the same seeds** (the 30 matched seeds, `common/config.py: MATCHED_SEEDS = 0..29`) means
the focal player faces identical co-player behaviour and identical pool dynamics in both arms, so
behavioural differences are attributable to the focal player rather than to its environment. The
co-player policies are:

| Policy | Behaviour |
|---|---|
| `cooperator` | Gathers when stock is low; shares 1 unit with a random living player once stock exceeds 4 |
| `free_rider` | Always gathers; hoards once the pool is empty; never shares |
| `tit_for_tat` | Shares like `cooperator`, but withholds (gathers) in any round after nobody shared with it — group-level reciprocity, since a 5-player commons has no single partner |
| `random` | Uniform over the valid actions; a null baseline, not a behavioural model |

### 4.1.4 Scenarios and scarcity severity

| Scenario | Rounds | Manipulation |
|---|---|---|
| `calm` | 10 | Control. Scarcity arises only from over-harvesting the pool |
| `drought` | 10 | Round 6 is a drought: gather yield drops from 3 to 1 and pool regeneration is multiplied by 0.3 |
| `repeated_trust` | 30 | Three consecutive 10-round blocks with the same players and no pool reset, so reciprocity in early blocks has consequences later. No scripted drought |

Orthogonally, **severity** *s* ∈ {0.0, 0.3, 0.5, 0.7, 0.9} scales pool regeneration every round
(*g′* = *g*·(1 − *s*)), giving a continuous dose–response axis instead of an on/off drought flag. It
stacks with the scripted drought in `drought` and is the only source of exogenous scarcity in
`repeated_trust`.

### 4.1.5 Logging

Every action by every player is one JSON row in a schema shared byte-for-byte between AI and human
logs (`LOGGING_SCHEMA.md`, enforced by `common/schema.py: validate_trial`): trial, agent, round,
scenario, action, target, message, resource before/after, alive, timestamp, plus a nested `meta`
block (seed, arm, severity, model, decision source, LLM parse-failure and rate-limit flags, token
counts). Logs are validated on write; a trial that fails validation is never written.

---

## 4.2 AI agent architecture

The AI focal player is a **two-layer hybrid**: a cheap reinforcement-learning *reflex* policy for
routine survival decisions, and an LLM *deliberation* layer invoked only when a decision has social
stakes. This mirrors a dual-process account of human decision-making and keeps LLM cost
proportional to the number of genuinely social decisions.

### 4.2.1 Reflex layer: PPO policy

`agents/rl_policy.py` trains a single PPO policy (Stable-Baselines3, MLP, `n_steps` = 256, batch
64, 100k timesteps, trained on `calm`). Its action space is restricted to the **non-social** actions
`gather`, `hoard`, `skip`, `move` — it never shares or communicates, so every social act in the AI
arm originates from the LLM layer. Its observation is a 6-dimensional vector: own stock, round
progress, drought flag, pool fill fraction, water received last round, and fraction of others
alive. Reward is the per-round change in own stock, with a −5 penalty on death.

Training uses **single-slot self-play**: one learner seat, with the other four seats driven by the
same live policy. This is a deliberate simplification of parameter-shared IPPO (which would push all
five seats' transitions into the buffer); it is sufficient because the policy's job is only to keep
itself alive, not to model opponents.

On 20 held-out seeds under `calm` (Gate D), the trained policy survives 100% of trials with mean
final stock 16.45, against 10% survival and mean final stock −0.90 for a uniform-random policy.

### 4.2.2 Deliberation layer: LLM

`agents/llm_reasoning.py` renders the focal player's observation as text — own stock, round,
drought status, shared-pool level, water received last round, and each other player's alive status
and last action — under a fixed system prompt that states the rules and discloses that co-players are
computer-controlled (the same disclosure human participants receive). The model returns a JSON
action; on a schema or validation error the call is retried once with the error appended, and on a
second failure the player **skips** and the row is flagged `meta.llm_parse_failure = true`. A
failure is never silently replaced by a random action — parse failures are data.

Provider rate-limit errors are flagged separately (`meta.llm_rate_limited`) and excluded from
parse-failure rates, so infrastructure quota is never reported as model behaviour. The primary model
is `openai/gpt-oss-20b` served by Groq at temperature 0.4. *[TODO once the campaign is run: final
model list, any secondary provider.]*

### 4.2.3 Arbitration

`agents/hybrid_agent.py: is_social_decision` routes a round to the LLM if any of the following
holds — otherwise the PPO policy acts:

- the player is **under resource pressure** (stock ≤ 4, i.e. two rounds of survival cost);
- it is a **drought round**;
- **someone shared with the player last round** (a live reciprocity opportunity).

The original design proposed spatial adjacency as a trigger; with no grid, every player is always
"adjacent", so adjacency would route every round to the LLM and defeat the purpose. Every row
records which layer made the decision (`meta.decision_source` = `rl` | `llm`).

### 4.2.4 Experimental arms

| Arm | Decisions made by | Role |
|---|---|---|
| `hybrid` | PPO, or LLM when `is_social_decision` fires | **Primary AI arm** |
| `rl_only` | PPO for every decision | Ablation: no social reasoning |
| `llm_only` | LLM for every decision | Ablation: no reflex layer |
| `llm_human_steered` | LLM with few-shot exemplars retrieved from human trials | Exploratory; kept separate from `llm_only` *[TODO: include only if run on real human data — see open issues]* |

### 4.2.5 Trial campaign

`agents/run_ai_trials.py` runs the full grid: the primary `hybrid` arm on every scenario × severity
cell at 100 seeds per cell; the ablation arms on every scenario at severities {0.0, 0.7} with 30
seeds per cell — 1,860 trials in total. Seeds 0–29 of every cell are the matched seeds shared with
human sessions. Each trial writes one JSONL file and one manifest entry recording the git SHA, model
name, a hash of the prompt-defining source file, the full environment configuration, and token
usage, so every trial can be traced to the exact code and prompt that produced it. The runner is
resumable and rate-limited across a worker pool.

*[TODO once the campaign is run: realised trials per cell, total LLM calls and tokens, parse-failure
rate, and the observed LLM routing rate per scenario. Pilot runs show the router never fires in
`calm` at severity 0 — the PPO policy keeps every player above the pressure threshold — so `hybrid`
and `rl_only` are behaviourally identical in that cell; this should be stated, not hidden.]*

### 4.2.6 Data quality assurance

Before analysis, every log (AI and human) is checked by `agents/qa_logs.py` for: schema validity;
stock continuity (each round's `resource_before` equals the previous round's `resource_after`);
consistency of `alive` with stock; no actions after death; no shares to players already dead; and
exactly one row per living player per round. It also reports trials and rows per scenario × arm and
the LLM parse-failure rate excluding rate-limited calls. *[TODO: final pass rate for the frozen
`ai_logs_v1` dataset.]*
