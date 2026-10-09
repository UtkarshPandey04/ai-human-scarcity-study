<div align="center">

# 🧠 AI–Human Behavioral Divergence Under Resource Scarcity

### *Behavioral Divergence Between LLM-Driven Multi-Agent Societies and Humans Under Resource Scarcity*

**When the water runs out, do AI agents behave like humans?**

A controlled Common Pool Resource (CPR) study investigating cooperation, defensive hoarding, strategic deception, trust, inequality, survival, and altruistic self-sacrifice in human and LLM-driven multi-agent societies.

![Python](https://img.shields.io/badge/Domain-Multi--Agent%20AI-3776AB)
![Research](https://img.shields.io/badge/Focus-Computational%20Social%20Science-6C5CE7)
![AI Safety](https://img.shields.io/badge/Research-AI%20Safety-00897B)
![Status](https://img.shields.io/badge/Status-Active%20Research-orange)

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Authors](#-authors)
- [Research Question](#-research-question)
- [Why This Matters](#-why-this-matters)
- [Research Contributions](#-research-contributions)
- [Experimental Environment](#-experimental-environment--scarcityenv)
- [Resource Dynamics](#-resource-dynamics)
- [Action Space](#-action-space)
- [Machine-Verifiable Communication](#-machine-verifiable-communication)
- [Experimental Design](#-experimental-design)
- [Experimental Conditions](#-experimental-conditions)
- [Hybrid AI Architecture](#-hybrid-ai-architecture)
- [Dataset](#-dataset)
- [Key Results](#-key-results)
- [Drought-Shock Results](#-drought-shock-results)
- [Repeated-Trust Results](#-repeated-trust-results)
- [Scarcity Dose–Response](#-n1--scarcity-dose-response)
- [Machine-Verifiable Deception](#-n2--machine-verifiable-deception)
- [Behavioral Distinguishability](#-n3--behavioral-distinguishability)
- [Behavioral Turing Test](#-behavioral-turing-test)
- [Qualitative Finding](#-qualitative-behavioral-finding)
- [Decision Latency](#-decision-latency)
- [Research Pipeline](#-research-pipeline)
- [Repository Structure](#-repository-structure)
- [Research Figures and Artifacts](#-research-figures-and-artifacts)
- [Live Research Application](#-live-research-application)
- [Statistical Analysis](#-statistical-analysis)
- [Reproducibility](#-reproducibility)
- [Limitations](#-limitations)
- [Scientific Integrity](#-scientific-integrity)
- [Future Work](#-future-work)
- [Planned Research Paper](#-planned-research-paper)
- [Citation](#-citation)
- [Contact](#-contact)

---

## 🔬 Overview

This project investigates whether Large Language Model (LLM)-driven agents reproduce human social behavior when essential shared resources become scarce.

The study implements a multi-agent **Common Pool Resource (CPR)** simulation in which five agents share a central freshwater lake. It compares human decision-making with a hybrid AI agent while keeping four companion policies fixed and matching experimental random seeds where specified.

Rather than evaluating only task completion or reasoning quality, the study measures observable behavior under pressure:

- 🤝 Cooperation and resource sharing
- 📉 Cooperation collapse as scarcity increases
- 🛡️ Defensive hoarding and resource retention
- 🎭 Strategic deception in structured messages
- 🔗 Reciprocity and alliance formation
- ⚖️ Resource inequality
- ❤️ Altruistic self-sacrifice
- ⏱️ Decision latency during crisis
- 🌧️ Society-level survival after a drought shock

> **Core idea:** An AI agent that appears cooperative under favorable conditions may not reproduce the complex social adaptations humans exhibit when scarcity becomes existential.

## 👥 Authors

**Research Mentor**

- **Ms. Laxmi** — Assistant Professor

**Student Researchers**

1. **Saksham Singh**
2. **Utkarsh Pandey**
3. **Sujal Kumar**
4. **Ms. Laxmi** — Research Mentor
5. **Yashash Tyagi**

**Department:** Computer Science & Engineering — Artificial Intelligence & Machine Learning  
**Institution:** KIET Deemed to be University, Delhi-NCR, Ghaziabad, Uttar Pradesh, India

> Author order should be confirmed by the research team before manuscript submission. The author list in the manuscript and the numbered affiliation block may use a different order.

---

## 🎯 Research Question

> **Do multi-agent systems driven by Large Language Models (LLMs) and Reinforcement Learning (RL) accurately reproduce human social dynamics when essential shared commons undergo severe existential scarcity shocks?**

The study examines whether the tested AI agents reproduce human responses such as cooperation collapse, defensive hoarding, strategic deception, reciprocity, inequality formation, altruistic self-sacrifice, and scarcity-induced deliberation.

### Research objectives

1. Compare human and AI behavior under matched shared-resource conditions.
2. Measure how increasing scarcity affects sharing and hoarding.
3. Audit structured resource claims against the environment's ground truth.
4. Compare resource inequality and survival across experimental conditions.
5. Test whether machine-learning models can distinguish human and AI behavioral trajectories.
6. Build a reproducible foundation for future research into socially aligned autonomous agents.

## 🌍 Why This Matters

Many AI evaluations focus on task completion, reasoning, coding, question answering, tool use, or individual decision-making. However, autonomous systems may increasingly operate in settings where multiple agents compete and cooperate over limited shared resources.

Potentially relevant settings include:

- Water and energy allocation
- Disaster response and emergency logistics
- Food distribution
- Public infrastructure
- Economic resource allocation
- Shared computing or network resources
- Crisis management and commons governance

The project studies whether the tested AI agents behave differently from the tested human participants when individual decisions affect collective survival. It does **not** assume that one simulated environment represents every human or AI system.

## 💡 Research Contributions

### N1 — Scarcity Dose–Response Analysis

Treats scarcity severity as a continuous variable and measures the change in sharing and hoarding as scarcity increases.

### N2 — Machine-Verifiable Deception Audit

Uses structured claims and environment state to identify mismatches between claimed and actual resource stock, reducing reliance on subjective annotation.

### N3 — Behavioral Distinguishability

Trains classifiers to predict whether a behavioral trajectory came from a human participant or an AI agent, then examines the features most associated with the prediction.

### Matched Focal-Player Substitution

Keeps four companion policies fixed while substituting the focal seat between a human participant and a hybrid AI agent under matched experimental seeds.

---

## 🏝️ Experimental Environment — `ScarcityEnv`

The study models a five-agent society sharing a central freshwater lake. The environment is inspired by Common Pool Resource research and the commons-governance tradition associated with Elinor Ostrom.

| Parameter | Specification |
|---|---|
| Agents per society | 5 |
| Shared resource | Freshwater lake |
| Lake carrying capacity, \(K\) | 50.0 |
| Intrinsic regeneration rate, \(r\) | 0.35 |
| Survival cost | 2 water units per agent per round |
| Death condition | Personal water stock falls below 0 |
| Over-demand handling | Proportional harvest scaling |
| Main environment | `ScarcityEnv` |

### 💧 Resource Dynamics

Lake regeneration follows a discrete logistic growth model:

\[
G(S_t)=rS_t\left(1-\frac{S_t}{K}\right)
\]

The resource stock is updated using the regeneration term and aggregate demand:

\[
S_{t+1}=S_t+rS_t\left(1-\frac{S_t}{K}\right)-D_t
\]

Where:

- \(S_t\) is the current lake stock.
- \(K=50.0\) is the maximum lake capacity.
- \(r=0.35\) is the intrinsic growth rate.
- \(D_t\) is aggregate demand requested from the shared resource.

If total demand exceeds available stock, each agent's harvest is scaled proportionally:

\[
Y_i=D_i\frac{S_t}{D_t}
\]

This avoids an arbitrary first-come-first-served queue and models over-extraction as a collective resource-allocation problem.

---

## 🎮 Action Space

Agents can perform five primary actions:

| Action | Description |
|---|---|
| `gather` | Request a harvest from the shared lake; the research specification lists a nominal yield of +3 water units before resource constraints. |
| `share(target, amount)` | Transfer personal water to another agent. |
| `hoard` | Preserve or ration personal reserves without drawing from the lake. |
| `skip` | Take no active action while still paying the survival cost. |
| `communicate(target, message)` | Send a structured message to another agent. |

## 💬 Machine-Verifiable Communication

Communication is structured so that claims can be checked against the actual environment state.

The prior project specification lists message types including:

```text
claim_stock(value)
promise_share(amount)
request(amount)
accuse
```

The research dossier also describes communication as structured tuples:

\[
\langle \text{kind},\text{value},\text{target},\text{surface}\rangle
\]

A resource claim is marked as deceptive when the claimed stock does not match the ground-truth resource state before the message:

\[
\text{Deception}=
\mathbb{I}(\text{Claimed Stock}\neq\text{Ground-Truth Resource Before})
\]

This operational definition supports automated auditing. It measures a defined mismatch; it does not independently establish an agent's subjective intent.

---

## 🧪 Experimental Design

### Matched Focal-Player Substitution

Four non-focal seats use fixed policies across matched conditions. Only the focal seat changes between a human participant and the hybrid AI agent.

```text
                  ┌──────────────────────┐
                  │     ScarcityEnv      │
                  │  Shared Water Pool   │
                  └──────────┬───────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
     Cooperator          Free-Rider        Tit-for-Tat
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                        Random Agent
                             │
                             ▼
                     ┌──────────────┐
                     │ Focal Player │
                     └──────┬───────┘
                            │
                   ┌────────┴────────┐
                   │                 │
                 Human               AI
```

### Fixed co-player policies

| Agent | Policy | Intended behavior |
|---|---|---|
| \(A_2\) | Cooperator | Shares surplus |
| \(A_3\) | Free-Rider | Gathers and does not share |
| \(A_4\) | Tit-for-Tat | Reciprocates prior cooperation |
| \(A_5\) | Random | Stochastic baseline |
| \(A_1\) | Experimental focal player | Human or AI |

### 🎯 Matched Random Seeds

The project dossier specifies matched random seeds:

```text
Seeds = 0 ... 29
```

The purpose is to expose the human and AI focal players to matched stochastic conditions, reducing variation from unrelated random events. The dossier describes a total of 84 trials; the exact mapping between seeds, conditions, and trial counts should be checked against the experiment logs.

## 🌡️ Experimental Conditions

### 1. Calm Baseline

**Duration:** 10 rounds

Measures baseline cooperation and spontaneous resource sharing under relatively abundant conditions.

### 2. Drought Shock

**Duration:** 10 rounds

At **Round 6**, a simulated drought reduces harvest yield by approximately **70%**.

Specified scarcity severity levels:

\[
\sigma \in \{0.0,0.5,0.7\}
\]

Measures:

- Cooperation collapse
- Defensive hoarding
- Deception
- Survival
- Alliance formation

### 3. Repeated Trust

**Duration:** 30 rounds

Examines long-horizon:

- Reciprocity and trust
- Cooperation and alliance formation
- Resource retention
- Inequality formation

---

## 🤖 Hybrid AI Architecture

The research dossier describes a two-layer agent architecture.

### Reflex layer — PPO

A Proximal Policy Optimization (PPO) policy handles routine action selection, such as gathering decisions and timing.

### Deliberation layer — LLM

An LLM reasoning component is invoked for selected high-stakes social events, including resource crises, drought shocks, or incoming unilateral gifts.

The dossier names the following providers and fallback path:

```text
Groq → Gemini → OpenRouter → Local Ollama (llama3.2)
```

The exact provider models, fallback behavior, and inference-cost claims depend on the implementation and deployment configuration. The intended design is to reduce dropped rounds when a remote provider is unavailable.

---

## 📊 Dataset

The current research dossier reports the following dataset size:

\[
\boxed{84\text{ trials}}
\]

| Group | Trials |
|---|---:|
| Human | 24 |
| AI | 60 |
| **Total** | **84** |

The project also reports:

\[
\boxed{5,320\text{ recorded action decisions}}
\]

Action decisions are not the same as independent participants or independent trials. Statistical analyses should use the correct unit of analysis and account for repeated observations where appropriate.

---

## 📈 Key Results

The tables below reproduce the reported results supplied with the project materials. They should be independently revalidated against the raw data and analysis scripts before publication or use as external claims.

### Human vs. AI — Pooled Results

| Metric | Human | AI | Mann–Whitney \(U\) | Reported \(p\) | Effect size |
|---|---:|---:|---:|---:|---|
| **Cooperation rate** | 0.251 ± 0.13 | 0.158 ± 0.05 | 963.0 | **0.0151** | Cliff's \(\delta=+0.338\); Cohen's \(d=+0.94\) |
| **Water shared** | 8.12 ± 9.73 | 5.63 ± 3.63 | 936.0 | **0.0306** | Cliff's \(\delta=+0.300\) |
| **Society Gini inequality** | 0.266 ± 0.17 | 0.108 ± 0.05 | 972.5 | **0.0096** | Cliff's \(\delta=+0.351\); Cohen's \(d=+1.26\) |
| **Pooled deception rate** | 0.125 ± 0.34 | 0.000 ± 0.00 | 810.0 | **0.0058** | Reported as statistically significant |
| **Decision latency** | 1,759 ms | 0 ms | 1,200.0 | **<0.0001** | Cliff's \(\delta=+0.667\) |

### 🌧️ Drought-Shock Results

| Metric | Human | AI | Mann–Whitney \(U\) | Reported \(p\) | Cliff's \(\delta\) |
|---|---:|---:|---:|---:|---:|
| **Hoarding rate** | 0.138 ± 0.10 | 0.046 ± 0.04 | 215.5 | **0.0037** | **+0.539** |
| **Deception rate** | 0.214 ± 0.42 | 0.000 ± 0.00 | 170.0 | **0.0357** | **+0.214** |
| **Society survival** | 0.611 ± 0.40 | 1.000 ± 0.00 | 70.0 | **0.0006** | **−0.500** |

The earlier README also reported an **alliance-count** comparison (Human 0.286, AI 1.400, \(p=0.0403\), Cliff's \(\delta=-0.375\)). This statistic was not included in the newer master dossier's pooled-results table and should be checked against the current analysis output before reuse.

### 🔥 Repeated-Trust Results

| Metric | Human | AI | Reported \(p\) | Cliff's \(\delta\) |
|---|---:|---:|---:|---:|
| **Society Gini inequality** | 0.453 | 0.053 | **0.0002** | **+1.000** |
| **Hoarding index** | 0.075 | 0.017 | **0.0030** | **+0.860** |

The reported repeated-trust results indicate a large difference in measured inequality and resource retention under the specific experimental configuration.

### Key observation

In the reported trials, human participants showed higher measured sharing and inequality, and more hoarding and deceptive resource claims during drought. The tested AI agents showed higher measured society-level survival in the drought condition. These are findings about the evaluated participants, policies, environment, and conditions—not universal claims about humans or AI.

---

## 💡 N1 — Scarcity Dose–Response

Scarcity is treated as a continuous variable rather than simply a binary condition.

### Cooperation / sharing

\[
\frac{\partial \text{Share}_{Human}}{\partial \sigma}=-0.1559
\]

\[
\frac{\partial \text{Share}_{AI}}{\partial \sigma}=-0.0072
\]

### Defensive hoarding

\[
\frac{\partial \text{Hoard}_{Human}}{\partial \sigma}=+0.1942
\]

\[
\frac{\partial \text{Hoard}_{AI}}{\partial \sigma}=-0.0959
\]

### Interpretation

The reported slopes indicate that human sharing decreases more steeply as scarcity increases, while human hoarding rises. The tested AI agents show a smaller change in sharing and a negative reported hoarding slope. These results motivate further tests across different populations, policies, and scarcity regimes.

---

## 🎭 N2 — Machine-Verifiable Deception

During drought shock, the dossier reports:

```text
Human deception: 21.4%
AI deception:      0.0%
```

The example describes a human message claiming to hold one unit while actually holding five, potentially discouraging requests from other agents.

The tested zero-shot/few-shot LLM agents produced no detected deception under this experiment's operational definition. This does not establish that all AI systems are incapable of deception in other environments.

---

## 🤖 N3 — Behavioral Distinguishability

A classifier was trained to predict whether a behavioral trajectory originated from a human or AI focal player.

### Random Forest

| Metric | Reported score |
|---|---:|
| Accuracy | **91.7%** |
| ROC-AUC | **0.940** |
| F1 score | **0.837** |
| Validation | 5-fold stratified cross-validation |

### Logistic Regression baseline

| Metric | Reported score |
|---|---:|
| Accuracy | **86.9%** |
| ROC-AUC | **0.897** |
| F1 score | **0.783** |

### Top behavioral features

| Feature | Reported value | Interpretation in the dossier |
|---|---:|---|
| Society Gini | 0.1821 permutation importance | Inequality patterns help distinguish trajectories |
| Cooperation rate | +1.7307 logistic weight | Higher value predicts Human |
| Alliance count | −1.5690 logistic weight | Higher value predicts AI when interpreted with the model's sign convention |
| Hoarding index | +1.5219 logistic weight | Higher value predicts Human |
| Arithmetic deception | +0.8371 logistic weight | Higher value predicts Human |

Classifier scores should be tested on held-out seeds, altered environments, and independent datasets before drawing conclusions about generalization. Feature weights and importance scores are model-specific associations, not causal explanations.

---

## 🧠 Behavioral Turing Test

The project describes a blinded human evaluation module in which participants inspect two behavioral trajectories and classify each as human- or AI-generated.

```text
Trajectory A → Human or AI?
Trajectory B → Human or AI?
```

The objective is to test whether observers can distinguish AI-generated behavioral trajectories from human trajectories. The available project brief describes this module but does not provide a completed result for the human evaluation, so no outcome is claimed here.

---

## ❤️ Qualitative Behavioral Finding

### The Altruistic Martyr

The dossier identifies one human trajectory as a qualitative example:

```text
Participant: PAB87
Trial:       drought_human_003_e49479
```

The participant reportedly gave away their remaining water during rounds 3–5 to keep other agents alive and died in Round 5.

This example illustrates a tension between individual survival and social or moral objectives. It should be treated as one observed trajectory, not as a general characterization of human behavior.

---

## ⏱️ Decision Latency

The research dossier reports a substantial increase in human decision latency during drought:

| Condition | Reported latency |
|---|---:|
| Calm | **2,450 ms** |
| Drought onset | **9,119 ms** |

Possible interpretations include additional deliberation, risk assessment, social conflict, moral uncertainty, and strategic reasoning. Latency alone does not directly measure any specific internal psychological state.

The pooled-results table separately reports average decision latency of 1,759 ms for Human and 0.0 ms for AI. The exact latency aggregation and timing instrumentation should be documented in the analysis code, especially if the AI value excludes inference or environment-processing time.

---

## 🧪 Statistical Analysis

The project materials report using:

- Mann–Whitney U tests
- Cliff's delta \((\delta)\)
- Cohen's \(d\)
- Stratified 5-fold cross-validation
- ROC-AUC
- F1 score
- Permutation feature importance
- Logistic regression feature weights

### Significance notation

```text
*    p < 0.05
**   p < 0.01
***  p < 0.001
```

Report exact p-values, effect sizes, uncertainty intervals, sample counts, and the unit of analysis wherever possible. A statistically significant result does not by itself establish practical importance or causality.

---

## 🔄 Research Pipeline

```text
                 ┌──────────────────────┐
                 │  Scarcity Environment│
                 │      ScarcityEnv     │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │  Shared Water Commons│
                 └──────────┬───────────┘
                            ▼
                ┌───────────┴───────────┐
                ▼                       ▼
         ┌─────────────┐         ┌─────────────┐
         │ Human Focal │         │  AI Focal   │
         │   Player    │         │ PPO + LLM   │
         └──────┬──────┘         └──────┬──────┘
                └───────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Structured Trial Logs│
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Feature Extraction   │
                 └──────────┬───────────┘
                            ▼
               ┌────────────┴────────────┐
               ▼                         ▼
        Statistical Tests         ML Classifiers
               │                         │
               └────────────┬────────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Human–AI Divergence  │
                 └──────────────────────┘
```

---

## 📁 Repository Structure

The previous project README describes the following artifacts. Confirm each path against the current repository before treating this tree as an exact inventory.

```text
ai-human-scarcity-study/
│
├── data/
│   ├── combined_scarcity_dataset.csv
│   ├── trial_features.csv
│   ├── scarcity_study.db
│   ├── llm_sft_dataset.jsonl
│   ├── trials/
│   │   └── *.jsonl
│   └── human_logs/
│       └── *.jsonl
│
├── models/
│   ├── distinguishability_classifier.json
│   └── human_clone_policy.json
│
├── paper/
│   ├── QUALITATIVE_FINDINGS.md
│   └── figures/
│       ├── fig1_behavioral_comparison.png
│       ├── fig2_dose_response.png
│       ├── fig3_distinguishability_roc.png
│       └── fig4_feature_importance.png
│
├── app/
│   └── Streamlit application
│
└── README.md
```

## 🖼️ Research Figures and Artifacts

The previous README lists the following planned or saved figures:

| Figure | Purpose |
|---|---|
| `fig1_behavioral_comparison.png` | Compare cooperation, hoarding, inequality, and survival |
| `fig2_dose_response.png` | Show behavioral response as scarcity severity increases |
| `fig3_distinguishability_roc.png` | Display ROC curves for behavioral classifiers |
| `fig4_feature_importance.png` | Visualize permutation importance and logistic regression weights |

### Research data and model artifacts

| Artifact | Path |
|---|---|
| Combined dataset | `data/combined_scarcity_dataset.csv` |
| Trial features | `data/trial_features.csv` |
| SQLite database | `data/scarcity_study.db` |
| AI trial logs | `data/trials/` |
| Human trial logs | `data/human_logs/` |
| LLM fine-tuning dataset | `data/llm_sft_dataset.jsonl` |
| Distinguishability model | `models/distinguishability_classifier.json` |
| Human-clone policy artifact | `models/human_clone_policy.json` |

These paths are retained from the previous README; their current availability should be verified in the repository.

---

## 🌐 Live Research Application

The previous README lists a Streamlit deployment for the human experimental interface:

**[Open the AI–Human Scarcity Study application](https://ai-human-scarcity-study.streamlit.app/)**

The application is described as an interactive environment through which human participants can perform experimental trials. Verify that the deployment is currently live and that the linked version matches the research dataset before sharing it publicly.

---

## 🧑‍🔬 Planned Research Paper

The planned manuscript structure includes:

1. Abstract
2. Introduction
3. Related Work
4. Experimental Framework
5. Empirical Methodology
6. Results
7. Discussion
8. Ethical Implications
9. Limitations
10. Future Work
11. Conclusion
12. References
13. Appendix / Supplementary Material

Related work identified in the research brief includes generative agents, multi-agent reinforcement learning in mixed-motive games, behavioral economics of scarcity, and LLM game-theory benchmarks. Formal citations and bibliographic details should be verified before manuscript submission.

---

## 🔁 Reproducibility

The project describes the following reproducibility mechanisms:

- Fixed random seeds
- Deterministic benchmark agents
- Matched human/AI environments
- Machine-verifiable communication
- Structured JSONL trial logs
- SQLite research database
- Explicit behavioral metrics
- Saved machine-learning model artifacts
- Research figures and statistical tables

For each run, document the environment configuration, seed, agent policies, model/provider version, prompts, data exclusions, package versions, and analysis script version. Keep raw data separate from derived features and results.

### Getting started

The supplied project materials do not specify verified dependency versions, a `requirements.txt` file, exact API environment-variable names, or a confirmed executable entry point. To avoid publishing misleading commands, use the setup instructions in the actual repository and add them here once verified.

Before running experiments:

1. Install the Python version and dependencies specified by the project.
2. Configure any required LLM provider credentials as local environment variables.
3. Never commit API keys, `.env` files, private participant data, or secrets.
4. Run a small environment smoke test.
5. Execute the documented trial script with a recorded seed.
6. Save raw logs and analysis outputs separately.
7. Run the statistical and classifier pipelines on the saved data.

---

## ⚠️ Limitations

This study should **not** be interpreted as demonstrating that all AI systems or all humans behave in a particular way.

Key limitations include:

- Limited human sample size and participant diversity
- An artificial simulated environment
- Dependence on specific LLM configurations, prompts, and PPO policies
- Dependence on the selected fixed companion-agent policies
- Potential trial-level statistical independence concerns
- Limited generalizability to real-world commons
- Possible leakage or overfitting in behavioral classification if validation splits are not designed carefully
- The need to verify all reported metrics against raw data and analysis scripts
- The fact that a detected mismatch between a claim and ground truth does not alone prove subjective intent

The appropriate scientific claim is:

> **The evaluated LLM-driven agents exhibited statistically distinguishable behavioral patterns from the tested human participants under the specified scarcity conditions.**

---

## 🧭 Scientific Integrity

The repository should clearly distinguish among:

### Measured results
Directly observed experimental outcomes.

### Statistical findings
Outputs from the documented statistical analysis pipeline.

### Interpretations
Potential explanations for the observed behavioral patterns.

### Hypotheses
Ideas requiring additional experiments.

### Future work
Experiments not yet performed.

**Do not fabricate missing experimental information.** If results, source files, or implementation details are unavailable, mark them as pending verification rather than presenting them as confirmed.

---

## 🚀 Future Work

### Larger human cohorts
Increase sample size and participant diversity.

### Cross-cultural replication
Test whether the observed patterns generalize across populations and contexts.

### More LLM families
Compare additional foundation models under identical protocols.

### Embodied agents
Introduce persistent energy, fatigue, memory, mortality, and resource needs.

### Human-trajectory fine-tuning
Explore supervised fine-tuning and in-context learning using ethically collected human scarcity trajectories, including the planned `data/llm_sft_dataset.jsonl` artifact.

### Fully autonomous societies
Replace frozen benchmark agents with agents capable of learning simultaneously.

### Long-horizon experiments
Extend simulations from 30 rounds to hundreds or thousands of interactions.

### Real-world commons
Explore carefully validated applications to water allocation, energy management, disaster response, food distribution, and public resources.

---

## 📖 Citation

A formal citation should be updated once the manuscript has been submitted or published. Until then, the following BibTeX entry is a **provisional manuscript citation**:

```bibtex
@article{pandey2026behavioral,
  title   = {Behavioral Divergence Between LLM-Driven Multi-Agent Societies and Humans Under Resource Scarcity},
  author  = {Pandey, Utkarsh and Kumar, Sujal and Singh, Saksham and Tyagi, Yash},
  year    = {2026},
  note    = {Research manuscript}
}
```

The research mentor and final author order should be included according to the team's confirmed authorship decision and target venue requirements.

---

## 📬 Contact

**Research Team**  
Department of Computer Science & Engineering — AI & ML  
KIET Deemed to be University  
Delhi-NCR, Ghaziabad, Uttar Pradesh, India

---

<div align="center">

## ⭐ Project Summary

> **When the water runs out, do AI agents behave like humans?**
>
> This study compares human and LLM-driven agents in a shared-resource environment where cooperation, competition, deception, trust, and survival collide. The reported trajectories reveal measurable behavioral divergence—particularly in scarcity adaptation, defensive hoarding, inequality, resource claims, and decision latency.
>
> The broader goal is to develop stronger benchmarks for evaluating whether autonomous AI systems reproduce human social dynamics under pressure, rather than only under favorable conditions.

**Status:** 🟡 Active Research  
**Domain:** Multi-Agent AI · LLMs · Computational Social Science · AI Safety  
**Institution:** KIET Deemed to be University

</div>
