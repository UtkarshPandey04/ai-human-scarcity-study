# Behavioral Divergence Between LLM-Driven Multi-Agent Societies and Humans Under Resource Scarcity
### Complete Research Guide: Setup to Publication

**Team:** Group 2 (Sujal & Utkarsh) → Human Study & Analysis (Streamlit interface, consent/ethics, recruitment, human trials)
Group 1 (Yashash & Saksham) → Simulation & AI Agents (environment, RL policy, LLM reasoning layer, AI trials)
---

## PHASE 0: Foundations (Week 1)

### 0.1 Tools everyone installs
- Python 3.10+, Git, GitHub account (shared repo)
- VS Code (or any IDE)
- `pip install stable-baselines3 gymnasium streamlit pandas numpy scipy scikit-learn shap matplotlib openai` (or your chosen LLM library)
- Access to an LLM: either a free-tier API (OpenAI, Groq, Gemini) or a local open-weight model (Ollama running Llama/Mistral) — pick based on budget

### 0.2 Repo structure (set this up Day 1, together)
```
project-root/
├── agents/              # Group 1
│   ├── environment.py
│   ├── rl_policy.py
│   ├── llm_reasoning.py
│   └── run_ai_trials.py
├── human_interface/     # Group 2
│   ├── app.py           # Streamlit app
│   ├── consent.py
│   └── logging_utils.py
├── data/
│   ├── ai_logs/
│   ├── human_logs/
│   └── LOGGING_SCHEMA.md
├── analysis/            # Joint
│   ├── feature_extraction.py
│   ├── stats_tests.py
│   └── classifier.py
├── dashboard/           # Joint
└── paper/
    └── draft.md
```

### 0.3 The Logging Schema (agree on this FIRST — everything depends on it)

Every action, from AI or human, gets logged as one row/JSON object:

```json
{
  "trial_id": "drought_round_ai_001",
  "source": "ai",              // "ai" or "human"
  "agent_id": "A1",
  "round": 6,
  "scenario": "drought",
  "action_type": "share",      // gather | share | hoard | move | skip
  "target_agent": "A2",        // null if not applicable
  "message_sent": "Take less today, I'll pay you back",
  "resource_before": 4,
  "resource_after": 6,
  "alive": true,
  "timestamp": "2026-09-01T10:32:00"
}
```

Both groups write to this exact schema. This is the single most important agreement your team makes.

---

## PHASE 1: Environment & Agents — Group 1 (Weeks 1–5)

### Step 1: Build the world (`environment.py`)
- Start with a 5x5 grid, one resource type (water), one regeneration rule.
- Define `step(actions)` function: takes all agents' actions, updates world state, returns new state + rewards.
- Add scripted events: e.g., round 6 = drought (resource output cut 70%).
- **Milestone check:** can you run 10 rounds with random actions and get a sensible log? If yes, move on.

### Step 2: Define the shared action space (`rl_policy.py` interface)
Actions: `gather`, `share(target)`, `hoard`, `move(direction)`, `skip`, `communicate(target, message)`.
Document this in a single `ACTIONS.md` file — Group 2's human interface must expose the identical set.

### Step 3: Add RL policy for reflexive actions
- Use Stable-Baselines3 PPO for movement/gathering decisions.
- Train on the environment alone first (no LLM yet) until agents reliably survive under normal (non-drought) conditions. This validates your environment is sane before adding complexity.

### Step 4: Add LLM reasoning layer (`llm_reasoning.py`)
- When an agent faces a "social" decision (share/hoard/ally/deceive), construct a prompt with: current resource state, visible other agents, round number, scenario context.
- Parse the LLM's response into a structured action + optional message.
- **Start simple:** a basic prompt like *"You are Agent A1 with 3 water units. Agents A2, A3 are nearby with 1 unit each. Decide: share, hoard, or skip. Respond in JSON: {action, target, message}."*
- Iterate on prompt design once basic loop works.

### Step 5: Run and log AI trials
- Run each scenario (calm, drought, repeated-trust) across multiple seeds (aim for 50-100 trials per scenario for statistical power).
- Save all logs to `data/ai_logs/` in the shared schema.

**Group 1 deliverable by end of Week 7:** clean, validated AI trajectory logs across 3+ scenarios.

---

## PHASE 2: Human Study — Group 2 (Weeks 1–7)

### Step 1: Learn Streamlit basics
- Simple grid rendering (can literally be colored boxes/emoji at first), buttons for each action, a text box for messages, a session-state counter for rounds.

### Step 2: Build participant flow
1. **Consent screen** — explain the study, what's recorded, that it's anonymous, get explicit agreement (required for ethics approval).
2. **Instructions screen** — explain rules, resource mechanics, action options (use the exact same wording/options as Group 1's action space).
3. **Game screen** — grid view, own resource level, action buttons, message box, round indicator.
4. **Debrief screen** — thank participant, explain study purpose (post-hoc, since revealing purpose beforehand could bias behavior).

### Step 3: Ethics approval — start this immediately, don't wait
- Draft: study purpose, procedure, risks (minimal — it's a game), data handling (anonymized, secure storage), consent form.
- Submit to your institute's ethics committee / your guide's process as early as Week 2. This is usually the slowest-moving part of the whole project — treat it as the critical path, not an afterthought.

### Step 4: Recruit participants
- Target: 25–30 people minimum, each playing 3-4 scenario variants (yields hundreds of decision data points).
- Sources: classmates, department mailing list, online (with guide's approval), Prolific/MTurk if budget allows and ethics approval covers it.

### Step 5: Run sessions and log
- Each session ~15-20 min. Log every action in the same schema as Group 1's AI logs, saved to `data/human_logs/`.

**Group 2 deliverable by end of Week 7:** clean human trajectory logs across the same scenarios AI agents ran.

---

## PHASE 3: Joint Analysis (Weeks 8–10, all 4 members)

### Step 1: Feature extraction (`analysis/feature_extraction.py`)
From raw logs (AI + human, same schema), compute per-trial metrics:
- **Hoarding index:** (resources kept) / (resources available)
- **Sharing rate:** fraction of rounds where `share` action taken
- **Deception rate:** compare `message_sent` claims against ground-truth resource state (did they lie about location/amount?)
- **Alliance formation rate:** repeated share/communicate pairs between same two agents
- **Survival rate:** % of agents alive at end of trial
- **Gini coefficient:** inequality of final resource distribution across agents

### Step 2: Statistical comparison (`analysis/stats_tests.py`)
- For each metric, run Mann-Whitney U test (non-parametric, safer than t-test for behavioral data) comparing AI trials vs. human trials.
- Report effect sizes, not just p-values — reviewers want to know *how much* they differ, not just *whether*.
- Build one clean comparison table: metric | AI mean | Human mean | p-value | effect size

### Step 3: The Distinguishability Classifier (`analysis/classifier.py`)
- Input: the behavioral feature vector per trial (hoarding index, sharing rate, etc.)
- Train a simple classifier (logistic regression or small random forest — don't overcomplicate) to predict AI vs. human.
- Report accuracy via cross-validation.
- Run SHAP to identify which features drive the distinction most — this becomes your key results figure.

### Step 4: Qualitative pass (optional but strengthens the paper)
- Pull 5-10 illustrative transcript excerpts (AI agent messages vs. human messages) that clearly show the divergence pattern (e.g., covert AI alliance vs. public human fairness proposal). Use these as quotes/examples in your Discussion section.

---

## PHASE 4: Dashboard (Week 9–10, whoever is strongest at frontend — likely Yashash, with help)

Build a simple visualization app (Streamlit or basic React) showing:
- Live/replay view of a simulation round
- Side-by-side AI vs. human metric comparison charts
- The classifier's SHAP feature-importance chart

This becomes your demo for defense/presentation and supplies your paper's figures.

---

## PHASE 5: Writing (Weeks 11–12)

### Suggested paper structure (~6-8 pages, standard format)
1. **Abstract** (150-200 words) — problem, method, key finding, one number
2. **Introduction** — the gap (no human-AI comparison exists for scarcity behavior), your contribution (3 bullet points max)
3. **Related Work** — Generative Agents (Park et al.), multi-agent RL survival work, behavioral economics (commons dilemma, public goods games) — explicitly state how you differ from each
4. **Methodology**
   - 4.1 Simulation environment & scenarios
   - 4.2 AI agent architecture (RL + LLM hybrid)
   - 4.3 Human study design & ethics
   - 4.4 Behavioral feature extraction
5. **Results**
   - Metric comparison table + statistical tests
   - Distinguishability classifier accuracy + SHAP chart
   - Qualitative examples
6. **Discussion** — what the divergence (or convergence) means, limitations (sample size, LLM choice, scenario simplicity)
7. **Future Work / Broader Impact** — AI safety auditing, disaster-response simulation, policy simulation, benchmark potential (you already have this drafted from earlier)
8. **Conclusion**

### Writing division
- Group 1 drafts Methodology 4.1–4.2
- Group 2 drafts Methodology 4.3–4.4
- Whoever ran the analysis drafts Results
- All 4 review and jointly write Introduction, Discussion, Future Work — these need whole-team perspective and are what reviewers read most carefully

---

## PHASE 6: Choosing Where to Publish

Realistic targets for a first paper like this (pick based on your timeline and guide's advice):
- **AI-for-Social-Good workshops** at major conferences (NeurIPS, ICML, AAAI often have these — lower barrier than main track, still credible)
- **National/regional AI or CS conferences** in your country
- **HCI-adjacent venues** if you lean into the human-study angle (CHI workshops, regional HCI conferences)
- **arXiv preprint** — post here regardless of where else you submit, establishes priority and makes it citable immediately

### Before submitting
- Run it past your guide for institutional co-authorship/approval requirements
- Check the venue's formatting template (usually LaTeX, e.g., ACL/IEEE style) — convert your draft early, don't leave formatting to the last day
- Get at least one outside read (a senior student or another faculty member) before submission

---

## Suggested Week-by-Week Timeline Summary

| Week | Group 1 | Group 2 | Joint |
|------|---------|---------|-------|
| 1 | Learn RL basics, start environment | Learn Streamlit, draft ethics form | Agree on logging schema, set up repo |
| 2 | Build grid world | Build consent/instructions screens | — |
| 3 | Define action space, start RL policy | Build game screen | Submit ethics approval |
| 4 | Train RL policy | Finish human interface | — |
| 5 | Build LLM reasoning layer | Recruit participants | — |
| 6 | Run AI trials | Run human trials | — |
| 7 | Finalize AI logs | Finalize human logs | — |
| 8 | — | — | Feature extraction |
| 9 | — | — | Stats + classifier |
| 10 | — | — | Dashboard build |
| 11 | — | — | Writing (split sections) |
| 12 | — | — | Joint review, submission prep |

---

## First Concrete Actions (do these this week)

1. Create the shared GitHub repo with the folder structure above.
2. All 4 members: install Python + tools, get access to your chosen LLM (API key or local model).
3. Sujal & Utkarsh: write a bare-bones `environment.py` that can run 5 rounds with random actions and print a log.
4. Yashash & Saksham: draft the ethics/consent form and send it to your guide for the approval process — start this now, it's the slowest step.
5. Whole team: 30-minute call to finalize the logging schema exactly as shown above, before any more code is written.
