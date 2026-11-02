# 🎓 Comprehensive Research Analysis, Paper Synthesis & Viva Defense Master Guide

**Paper Title:** *Behavioral Divergence Between LLM-Driven Multi-Agent Societies and Humans Under Resource Scarcity*  
**Research Team:** Utkarsh Pandey$^1$, Saksham Singh$^2$, Sujal Kumar$^3$, Yashash Tyagi$^4$, Ms. Laxmi$^5$ (Research Mentor & Assistant Professor)  
**Affiliation:** Department of Computer Science & Engineering (AI & ML), Krishna Institute of Engineering & Technology (KIET Deemed to be University), Ghaziabad, Delhi-NCR, Uttar Pradesh, India.  
**Repository:** [github.com/UtkarshPandey04/ai-human-scarcity-study](https://github.com/UtkarshPandey04/ai-human-scarcity-study)

---

## 📌 Executive Summary for Viva & Defense

| Core Attribute | Specification / Finding |
|---|---|
| **Core Research Question** | Do multi-agent systems driven by Large Language Models (LLMs) and Reinforcement Learning (RL) reproduce human social dynamics when shared common-pool resources undergo severe existential scarcity shocks? |
| **Short Answer** | **No.** Humans exhibit highly elastic behavior (surges in hoarding to 0.71, collapse of cooperation to 0.044, selective inequality, and 14.3%–27.3% strategic deception), whereas AI agents exhibit rigid, mechanical, and myopic routines. |
| **Analyzed Dataset ($N=112$)** | **52 Human trials** (37 real human drought sessions: 30 single-round, 7 multi-round; 15 scripted human proxy) vs. **60 AI trials** (15 matched runs each of 4 canonical policies: Cooperator, Tit-for-Tat, Random, Free-Rider). |
| **Expanded Campaign** | A separate **959-trial** RL/hybrid/LLM campaign (`meta.arm="rl_only"`, `hybrid`, `llm_only`) frozen with 0 rate-limited calls and 0 parse errors across 234 LLM calls. |
| **Distinguishability (Model A)** | Supervised classifier separates Human vs. AI trials with **89.3% accuracy (0.906 ROC-AUC)** on behavioral features alone, and **97.3% accuracy (0.973 ROC-AUC)** when adding deception and latency cues (53.6% majority floor). |
| **Behavioral Cloning (Model B)** | Softmax imitation learning policy $P(\text{action} \mid \text{state})$ achieves **75.4% action agreement** on 321 human decision steps (69.8% majority class floor). |
| **Strategic Deception (RQ2)** | **14.3% (3 of 21)** of human stock claims were false (Wilson 95% CI: 5.0%–34.6%); in drought, **27.3% (3 of 11)** were false. AI baselines made 0 claims (0% deception). |

---

## 1. Research Problem, Gap & Contributions

### The Problem
Autonomous LLM agents are rapidly being deployed as decision-makers in shared-resource settings:
- Distributed supply chain negotiations
- Disaster logistics and emergency food/water distribution
- Autonomous vehicle dispatch and energy grid load shedding
- Decentralized finance (DeFi) liquidity pools

Current systems assume that LLM agents converge to **human-like cooperative equilibria**. However, behavioral economics shows that existential scarcity triggers **cognitive tunneling, future discounting, defensive hoarding, and reduced honesty**. If AI agents fail to reproduce this behavioral signature, systems designed assuming human-like compliance will experience catastrophic collective failure when resources are contested.

### The Scientific Gap in Prior Literature
1. **Survival Games (Chen et al., 2025):** Blends two humans and one LLM in an unstructured narrative without frozen control baselines or quantitative distinguishability metrics.
2. **DECIDE-SIM (Mohamadi & Yavari, 2025):** Evaluates eleven LLMs in survival environments but includes **zero human participants**, making human-AI comparison impossible.
3. **Dyadic Economic Games (Akata et al., 2023; Niszczota et al., 2025):** Focuses on 2-player matrix games (Prisoner's Dilemma) that lack a shared, depletable common pool resource.
4. **Generative Agents (Park et al., 2023):** Generates believable social routines in "Smallville" but operates under infinite abundance with zero survival stakes.

### Key Contributions of this Work
1. **Focal-Player Substitution Protocol:** Holds the 4-agent co-player ecologies strictly fixed across matched random seeds ($0 \dots 29$), alternating only the 5th focal seat between Human and AI.
2. **Slotted Communication & Arithmetic Deception:** Operationalizes deception as a verifiable mathematical mismatch:
   $$\text{Deception} = \mathbb{I}(\text{Claimed Stock} \neq \text{Ground-Truth Resource Before})$$
   Eliminates subjective human or LLM annotation bias.
3. **Hybrid AI Architecture:** PPO fast reflex layer for routine gathering + multi-provider LLM deliberation layer (`Groq` $\rightarrow$ `OpenRouter` $\rightarrow$ `Gemini` $\rightarrow$ `Ollama Llama-3.2`) with observation caching and key pooling.
4. **Behavioral Distinguishability (Behavioral Turing Test):** Demonstrates that human and AI behavioral trajectories are mathematically separable in feature space ($0.940 - 0.973$ ROC-AUC).

---

## 2. Experimental Environment: `ScarcityEnv`

The study models a 5-agent society sharing a common freshwater lake inspired by Elinor Ostrom's Common Pool Resource (CPR) governance principles:

### Dynamic Resource Equations
Lake volume follows discrete logistic regeneration:
$$S_{t+1} = S_t + r S_t \left(1 - \frac{S_t}{K}\right) - D_t$$

Where:
- $S_t$: Lake stock at round $t$.
- $K = 100.0$: Maximum lake carrying capacity.
- $r = 0.40$: Intrinsic regeneration rate.
- $D_t$: Total harvest demand across all 5 agents.
- **Survival Cost:** 2 water units per agent per round. An agent whose private reserve drops below 0 is eliminated (death).
- **Over-harvesting / Proportional Scaling:** When aggregate draw exceeds available lake stock ($D_t > S_t$), each agent's harvest is scaled proportionally:
  $$Y_i = D_i \cdot \frac{S_t}{D_t}$$
  *(Prevents first-come-first-served order bias and models collective tragedy of the commons).*

### Maximum Sustainable Yield (MSY)
A scarcity severity shock $\sigma \in [0.0, 1.0]$ reduces the effective growth rate to $r(1 - \sigma)$:
$$\text{MSY} = \frac{r(1 - \sigma) K}{4}$$

| Scarcity Severity ($\sigma$) | Effective Growth Rate | MSY (units/round) | Society Requirement (5 agents $\times$ 2 units) | Sustainability Status |
|:---:|:---:|:---:|:---:|:---|
| **$\sigma = 0.0$ (Calm)** | $0.40$ | **$10.0$** | $10.0$ | Sustainable equilibrium |
| **$\sigma = 0.3$** | $0.28$ | **$7.0$** | $10.0$ | Mild deficit |
| **$\sigma = 0.5$** | $0.20$ | **$5.0$** | $10.0$ | Moderate collapse |
| **$\sigma = 0.7$ (Drought)** | $0.12$ | **$3.0$** | $10.0$ | **Severe deficit (Collapse imminent)** |
| **$\sigma = 0.9$** | $0.04$ | **$1.0$** | $10.0$ | Critical extinction |

> **Key Observation:** Because 5 agents require 10 units per round to survive, any $\sigma > 0$ pushes the sustainable yield below the society's metabolic requirement. Unrestrained gathering inevitably collapses the commons; survival requires strict restraint and sharing.

---

## 3. Experimental Methodology & Focal Substitution

### Focal Substitution Design
```
                        ┌────────────────────────┐
                        │      ScarcityEnv       │
                        │ 5-Seat Depletable Pool │
                        └───────────┬────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
       Cooperator              Free-Rider               Tit-for-Tat
   (Shares surplus)        (Gathers, no share)     (Reciprocates prior)
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    ▼
                               Random Agent
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Focal Seat $A_1$    │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
               Human Participant             AI Agent
              (Matched Seeds 0-29)     (Matched Seeds 0-29)
```

### 3 Experimental Scenarios
1. **Calm Baseline Condition:** 10 rounds, seeds 0–29, $\sigma = 0.0$ (no perturbation).
2. **Drought Scarcity Condition:** 10 rounds, seeds 0–29, round-6 shock: nominal harvest yield cuts from $3 \rightarrow 1$ unit, regeneration rate cuts $\times 0.3$ ($\sigma = 0.7$).
3. **Repeated-Trust Condition:** 30 rounds, seeds 0–29, long horizon testing sustained reciprocity and wealth consolidation.

---

## 4. Empirical Results (Exact Manuscript Numbers)

### Composition of the 112 Analyzed Trials (Table IV)
- **Real Human Single-Round (Drought):** 30 trials
- **Real Human Multi-Round (Drought):** 7 trials
- **Human Scripted Proxy (Calm, Drought, Trust):** 15 trials
- **AI Baselines (Cooperator, Tit-for-Tat, Random, Free-Rider):** 15 trials each = 60 trials
- **Total Analyzed Set:** **112 trials** (52 Human, 60 AI)

---

### Real Human Sessions ($n=37$) vs. Pooled AI Baselines ($n=60$) (Table V)

| Metric | Human Mean (SD) | AI Mean (SD) | Cliff's Delta ($\delta$) | $p$-value (Mann-Whitney) | Interpretation |
|---|:---:|:---:|:---:|:---:|:---|
| **Cooperation Rate** | $0.044$ | $0.158$ | **$-0.53$** | $3 \times 10^{-6}$ | Humans cooperate less under drought crisis |
| **Gather Rate** | $0.884$ | $0.662$ | **$+0.58$** | $8 \times 10^{-7}$ | Humans prioritize aggressive gathering |
| **Retained Wealth Index** | $0.710$ | $0.206$ | **$+0.71$** | $2 \times 10^{-9}$ | Large effect: Humans hoard defensive reserves |
| **Society Gini Index** | $0.199$ | $0.108$ | **$+0.43$** | $2 \times 10^{-4}$ | Humans tolerate and create wealth disparity |
| **Alliance Count** | $0.00$ | $2.15$ | **$-0.57$** | $4 \times 10^{-8}$ | Multi-round alliances non-existent in short sessions |

---

### Per-Policy AI Baselines vs. Real Humans (Table VI)

| Focal Policy | Cooperation Rate | Retained Wealth | Society Gini | Alliances | Survival Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Cooperator ($n=15$)** | $0.371$ | $0.116$ | $0.163$ | $6.47$ | $1.00$ ($100\%$) |
| **Tit-for-Tat ($n=15$)** | $0.109$ | $0.298$ | $0.053$ | $1.47$ | $0.73$ ($73\%$) |
| **Random ($n=15$)** | $0.152$ | $0.018$ | $0.217$ | $0.67$ | $0.13$ ($13\%$) |
| **Free-Rider ($n=15$)** | $0.000$ | $0.392$ | $0.000$ | $0.00$ | $1.00$ ($100\%$) |
| **Real Human Sessions ($n=37$)** | **$0.044$** | **$0.710$** | **$0.199$** | **$0.00$** | **$0.84$ ($84\%$)** |

> **Key Scientific Takeaway:** Humans behave closest to the **Free-Rider** in retained wealth ($0.710$) and cooperation ($0.044$). However, unlike Free-Riders, humans actively utilize **strategic deception** and **moral deliberation**.

---

### RQ2: Strategic Deception Findings
- **Overall Human Claims:** 21 total stock claims made.
- **Deceptive Claims:** **3 were false** ($14.3\%$, Wilson 95% CI: $5.0\% - 34.6\%$).
- **Drought Specific:** Under drought shock, **3 of 11 claims were false ($27.3\%$)**.
- **AI Baselines:** **0 claims made (0% deception)**. This zero deception is structural—scripted bots and standard zero-shot LLMs do not spontaneously initiate deceptive bluffs.

---

### RQ3: Distinguishability Classifier Ablation (Table VII)
Evaluated on 112 trials with stratified 5-fold cross-validation (53.6% majority floor):

| Feature Set | 5-Fold CV Accuracy | ROC-AUC Score | Scientific Inference |
|---|:---:|:---:|---|
| **Behavioral Features Only** | **$89.3\%$** | **$0.906$** | Strong mathematical separation purely from game actions |
| **+ Deception Feature** | **$92.0\%$** | **$0.957$** | False claims provide high-signal human indicator |
| **+ Latency Feature** | **$94.6\%$** | **$0.933$** | Decision timing reflects human deliberation |
| **+ Both (Full Feature Set)** | **$97.3\%$** | **$0.973$** | Near-perfect separation against 53.6% majority floor |
| **Majority Class Floor** | $53.6\%$ | $0.500$ | Random / baseline guessing rate |

*Robustness Check:* Dropping the 15 scripted proxy trials leaves 97 trials (61.9% majority floor). The classifier still reaches **93.7% accuracy (0.918 AUC)** on behavioral features alone and **96.9% accuracy (0.978 AUC)** with deception and latency.

---

### Standardized Logistic Regression Feature Weights (Figure 6)
Directional weights driving the classifier ($+ = \text{Human}$, $- = \text{AI}$):
1. **Retained Wealth Index:** $\mathbf{+1.85}$ (Largest weight toward **Human**)
2. **Decision Latency:** $\mathbf{+1.22}$ (Spike in reaction time toward **Human**)
3. **Deception Rate:** $\mathbf{+0.84}$ (Misreporting stock toward **Human**)
4. **Society Gini Index:** $\mathbf{+0.52}$ (Higher wealth disparity toward **Human**)
5. **Gather Rate:** $\mathbf{+0.35}$ (Prioritizing extraction toward **Human**)
6. **Cooperation Rate:** $\mathbf{-0.48}$ (Lower cooperation points toward **Human**)
7. **Alliance Count:** $\mathbf{-1.15}$ (Mechanical reciprocity points toward **AI**)

---

## 5. Visual Atlas of All Graphs & Figures (Paper, Manuscript & Researcher Portal)

This section provides an exhaustive technical and behavioral description of **every single graph** in the academic paper, the manuscript draft, and the live **Researcher Portal**.

```
Complete Visualization Inventory:
├── PART A: The 8 Publication-Ready Camera Figures (300 DPI - paper/figures/)
│   ├── Figure 1: Behavioral Metric Distributions (Share, Hoard, Gini, Cooperation)
│   ├── Figure 2: Scarcity Dose-Response Elasticity Curves (Novelty N1 - 2 Panels)
│   ├── Figure 3: Distinguishability ROC-AUC Across Scenarios (Novelty N3)
│   ├── Figure 4: Feature Importance Drivers (RF Permutation vs. Logistic Weights)
│   ├── Figure 5: Survival Hazard & Rounds Survived (2 Panels)
│   ├── Figure 6: Strategic Communication Honesty vs. Deception (Novelty N2 - 2 Panels)
│   ├── Figure 7: Cognitive Deliberation Latency Distribution (Reaction Time Boxplot)
│   └── Figure 8: Behavioral Cloning Alignment Vector vs. Human Target
│
├── PART B: The IEEE 6-Page Paper Manuscript Figures (Figures 1–6)
│   ├── Paper Fig 1: Sustainable Yield MSY Curve vs. Real Drought Trajectory
│   ├── Paper Fig 2: Architectural Data Pipeline & State Transition
│   ├── Paper Fig 3: Human (Real Sessions) vs. Per-Policy AI Baselines (95% Bootstrap CIs)
│   ├── Paper Fig 4: Retained-Wealth Index vs. Focal Survival Rate Distributions
│   ├── Paper Fig 5: 5-Fold Cross-Validated Classifier Ablation & ROC Curves
│   └── Paper Fig 6: Standardized Logistic Weights & Round-by-Round Drought Action Mix
│
└── PART C: The Live Researcher Portal Interactive Charts (dashboard/researcher_hub.py)
    ├── Tab 1: Scenarios Distribution Bar Chart (fig_sc)
    ├── Tab 1: Behavioral Action Profile Grouped Bar Chart (fig_act)
    ├── Tab 1: Mean Cognitive Latency by Scenario Bar Chart (fig_lat)
    ├── Tab 1: Round-by-Round Commons Depletion Trajectory (pivot_r)
    ├── Tab 1: Society Wealth Inequality Gini Comparison (fig_gini)
    ├── Tab 2: Live Multi-LLM Diagnostic Ping Round-Trip Latency Chart
    ├── Tab 2: Human Decision Latency Histogram Distribution (fig_h_lat)
    ├── Tab 2: Policy Social Dynamics: Share % vs. Hoard % (fig_social)
    ├── Tab 2: Scarcity Survival Resilience by Policy (fig_surv)
    ├── Tab 5: Human Decision Step Counts for Imitation Learning (fig_acts)
    └── Tab 6: Real-Time Softmax Forward Inference Probability Chart (fig_prob)
```

---

### PART A: Detailed Analysis of the 8 Publication Figures (`paper/figures/`)

#### 📈 Figure 1: Behavioral Metric Distributions Across Scenarios (`fig1_behavioral_comparison.png`)
* **File Location:** `paper/figures/fig1_behavioral_comparison.png` (300 DPI, $16 \times 4.2$ inches)
* **Visual Structure:** 4-panel multi-plot across 3 scenarios: *Calm Baseline*, *Drought Scarcity*, and *Repeated-Trust*.
  - **Panel 1 (Sharing Rate):** Y-axis $[0, 0.45]$. In Calm, humans share at $24.0\%$ vs. AI $17.0\%$. Under Drought, human sharing collapses to $5.6\%$ vs. AI $15.5\%$. In Trust, human sharing recovers to $26.7\%$ vs. AI $15.0\%$.
  - **Panel 2 (Hoarding Rate):** Y-axis $[0, 0.35]$. In Calm, human hoarding is $0.0\%$ vs. AI $4.6\%$. Under Drought, human hoarding surges ($13.8\%$ rate, $0.658$ index) while AI hoarding remains flat ($4.6\%$).
  - **Panel 3 (Society Gini Index):** Y-axis $[0, 0.60]$. In Calm, Human Gini is $0.403$ vs. AI $0.148$. In Drought, Human Gini is $0.215$ vs. AI $0.124$. In Repeated-Trust, Human Gini reaches **$0.453$** vs. AI **$0.053$** ($\text{Cliff's } \delta = \mathbf{+1.000}$).
  - **Panel 4 (Cooperation Rate):** Y-axis $[0, 0.50]$. In Calm, Human cooperation is $34.0\%$ vs. AI $17.0\%$. In Drought, Human cooperation collapses to $6.7\%$ vs. AI $15.5\%$.
* **Visual Styling:** Human bars in Navy Blue (`#1b5fa8`), AI bars in Vermilion Orange (`#d95f02`), with $\pm 1\text{ SD}$ error bars and percentage text labels above bars.
* **Viva Takeaway:** *Proves that human cooperation is high in safety but collapses under crisis, whereas AI is rigidly flat.*

---

#### 📉 Figure 2: Scarcity Dose-Response Elasticity Curves (Novelty N1) (`fig2_dose_response.png`)
* **File Location:** `paper/figures/fig2_dose_response.png` (300 DPI, $11 \times 4.5$ inches)
* **Visual Structure:** 2 continuous slope panels plotting behavioral response across continuous severity $\sigma \in [0.0, 0.7]$.
  - **Panel A (Sharing Rate vs. Severity $\sigma$):**
    - Human curve: Solid navy line starting at $0.240$ ($\sigma=0.0$) and steeply dropping to $0.056$ ($\sigma=0.7$). Empirical slope: $\frac{\partial \text{Share}}{\partial \sigma} = \mathbf{-0.1559 \text{ to } -0.3093}$.
    - AI curve: Dashed orange line starting at $0.170$ and ending at $0.155$. Empirical slope: $\frac{\partial \text{Share}}{\partial \sigma} = \mathbf{-0.0072}$ (virtually horizontal).
  - **Panel B (Hoarding Rate vs. Severity $\sigma$):**
    - Human curve: Starts at $0.000$ and rises sharply to $0.138$ (index $0.658$). Empirical slope: $\frac{\partial \text{Hoard}}{\partial \sigma} = \mathbf{+0.0577 \text{ to } +0.1942}$.
    - AI curve: Starts at $0.046$ and remains flat/negative at $0.046$. Empirical slope: $\frac{\partial \text{Hoard}}{\partial \sigma} = \mathbf{-0.0959}$.
* **Viva Takeaway:** *Novelty N1 replaces binary 'before/after' claims with continuous derivatives, demonstrating the lack of psychological elasticity in AI models.*

---

#### 🎯 Figure 3: Distinguishability ROC-AUC Across Scarcity Levels (`fig3_distinguishability_roc.png`)
* **File Location:** `paper/figures/fig3_distinguishability_roc.png` (300 DPI, $8 \times 4.5$ inches)
* **Visual Structure:** Grouped bar chart comparing classification ROC-AUC across 4 subsets:
  - *Pooled (All Scenarios):* Logistic Regression AUC = **$0.897$**, Random Forest AUC = **$0.940$**.
  - *Calm Condition ($\sigma=0.0$):* Logistic Regression AUC = **$1.000$**, Random Forest AUC = **$1.000$** (Perfect separation).
  - *Drought Condition ($\sigma=0.7$):* Logistic Regression AUC = **$0.879$**, Random Forest AUC = **$0.921$**.
  - *Repeated-Trust Condition:* Logistic Regression AUC = **$1.000$**, Random Forest AUC = **$1.000$** (Perfect separation).
  - Reference: Gray horizontal dashed line at $\text{AUC} = 0.50$ (chance baseline).
* **Viva Takeaway:** *Proves Novelty N3: behavioral feature vectors provide a mathematical fingerprint allowing a classifier to separate humans from AI far above the 53.6% majority floor.*

---

#### 🌲 Figure 4: Feature Importance Drivers & Attribution (`fig4_feature_importance.png`)
* **File Location:** `paper/figures/fig4_feature_importance.png` (300 DPI, $12 \times 5$ inches)
* **Visual Structure:** 2 horizontal bar panels identifying the key features driving the classifier.
  - **Panel A (Random Forest Permutation Importance):** Measures mean decrease in accuracy when a feature is randomly shuffled.
    1. *Society Gini Index:* **$0.1821$** (Top predictive feature)
    2. *Cooperation Rate:* **$0.1410$**
    3. *Hoarding Index:* **$0.1245$**
    4. *Decision Latency:* **$0.0980$**
    5. *Gather Rate:* **$0.0812$**
  - **Panel B (Logistic Regression Directional Weights):**
    - Blue bars pointing right ($+$, predicts **Human**):
      - *Society Gini:* $+1.29$ to $+1.85$
      - *Decision Latency:* $+1.12$ to $+1.22$
      - *Deception Rate:* $+0.84$
      - *Gather Rate:* $+0.35$
    - Orange bars pointing left ($-$, predicts **AI**):
      - *Alliance Count:* $-1.02$ to $-1.15$ (rigid reciprocity indicates AI)
      - *Skip Rate:* $-1.11$ (idling indicates AI)
      - *Cooperation Rate:* $-0.48$ (uniform unhedged cooperation indicates AI)
* **Viva Takeaway:** *Inequality patterns, moral latency, and deception are distinct human signatures; mechanical reciprocity and idling predict AI.*

---

#### 🛡️ Figure 5: Survival Rates & Longevity Hazard (`fig5_survival_hazard_curves.png`)
* **File Location:** `paper/figures/fig5_survival_hazard_curves.png` (300 DPI, $11 \times 4.5$ inches)
* **Visual Structure:** 2 panels comparing society longevity.
  - **Panel A (Focal Survival Rate %):**
    - Calm: Humans $96\% - 100\%$ vs. AI $100\%$.
    - Drought: Humans $61.1\% - 85.7\%$ vs. AI $95\% - 100\%$.
    - Repeated-Trust: Humans $100\%$ vs. AI $55.0\%$.
  - **Panel B (Mean Rounds Completed out of 10):**
    - Calm: Humans $9.8$ rounds vs. AI $10.0$ rounds.
    - Drought: Humans $7.8$ rounds vs. AI $9.6$ rounds.
    - Repeated-Trust: Humans $30.0$ rounds vs. AI $18.4$ rounds.
* **Viva Takeaway:** *In drought, AI survives longer because it mechanically harvests the remaining pool without hesitation; in 30-round Trust, humans survive 100% because reciprocal alliances protect the society over long horizons.*

---

#### 🎭 Figure 6: Strategic Communication Honesty vs. Deception (Novelty N2) (`fig6_communication_deception_matrix.png`)
* **File Location:** `paper/figures/fig6_communication_deception_matrix.png` (300 DPI, $11 \times 4.5$ inches)
* **Visual Structure:** 2 panels auditing structured claims against ground truth.
  - **Panel A (Human Message Volume):**
    - Calm: $10$ Honest claims, $0$ Deceptive claims.
    - Drought: $8$ Honest claims, **$3$ Deceptive claims** ($27.3\%$ deception rate).
    - Repeated-Trust: $11$ Honest claims, $0$ Deceptive claims.
  - **Panel B (Deception Rate % by Arm):**
    - Human Deception: $0.0\%$ in Calm, **$21.4\% - 27.3\%$ in Drought**, $0.0\%$ in Trust.
    - AI Deception: **$0.0\%$ across all conditions**.
* **Viva Takeaway:** *Deception is not random noise—it emerges exclusively during drought as an adaptive strategy to protect private reserves from being drained by others.*

---

#### ⏱️ Figure 7: Cognitive Deliberation Latency Distribution (`fig7_cognitive_deliberation_latency.png`)
* **File Location:** `paper/figures/fig7_cognitive_deliberation_latency.png` (300 DPI, $8 \times 4.5$ inches)
* **Visual Structure:** Boxplot distribution of human reaction times in milliseconds across Calm, Drought, and Repeated-Trust, plotted against a gray dotted reference line at $2,000\text{ ms}$.
  - Calm Baseline: Median reaction time $\approx 2,450\text{ ms}$ (IQR $1,800 - 3,100\text{ ms}$).
  - Drought Scarcity Shock: Median reaction time spikes to **$9,119\text{ ms}$** (upper outliers reaching $14,000\text{ ms}$).
  - Repeated-Trust: Reaction time settles to $\approx 2,100\text{ ms}$ once alliances stabilize.
* **Viva Takeaway:** *Reaction time is a physical proxy for cognitive load. Under crisis, humans pause to weigh the moral cost of sharing vs. personal self-preservation.*

---

#### 🔄 Figure 8: Behavioral Cloning Alignment Vector vs. Human Target (`fig8_steering_alignment_vector.png`)
* **File Location:** `paper/figures/fig8_steering_alignment_vector.png` (300 DPI, $8.5 \times 4.5$ inches)
* **Visual Structure:** Grouped bar chart comparing the empirical human action target against the trained Behavioral Cloning policy (`models/human_clone_policy.json`).
  - Gather: Human target $69.8\%$, Cloned Model $69.9\%$.
  - Share: Human target $20.8\%$, Cloned Model $20.8\%$.
  - Hoard: Human target $4.0\%$, Cloned Model $4.0\%$.
  - Communicate: Human target $4.7\%$, Cloned Model $4.7\%$.
* **Viva Takeaway:** *Proves that empirical human scarcity data can successfully train steerable imitation-learning models that close the behavioral fidelity gap.*

---

### PART B: The IEEE 6-Page Paper Manuscript Figures (Figures 1–6)

#### 📉 Paper Figure 1: Sustainable Yield MSY vs. Drought Trajectory (Page 2)
* **Left Panel:** Plots the theoretical $\text{MSY} = \frac{r(1-\sigma)K}{4}$ curve across $\sigma \in \{0.0, 0.3, 0.5, 0.7, 0.9\}$ showing sustainable yields of $10, 7, 5, 3, 1$ units/round.
* **Right Panel:** Empirical focal player water reserves across rounds 1–10 in drought (shock at round 6). The human curve falls below the AI baseline after round 2 because human multi-round sessions experience faster depletion.

#### 🏗️ Paper Figure 2: System Pipeline (Page 2)
* Architectural diagram mapping: `ScarcityEnv` (5-seat pool) $\rightarrow$ 1 focal seat (Human/AI) + 4 frozen policies (C, F, T, R) $\rightarrow$ JSONL validated logs $\rightarrow$ SQLite tables (`trials`, `actions`) $\rightarrow$ Feature extractor $\rightarrow$ Statistical tests & ML classifier.

#### 🤝 Paper Figure 3: Human vs. Per-Policy AI Baselines (Page 4)
* 4-panel bar charts with **95% bootstrap confidence intervals** comparing real humans ($n=37$) against the 4 scripted policies:
  - *Cooperation Rate:* Cooperator ($0.371$), Free-Rider ($0.000$), Human ($0.044$).
  - *Retained-Wealth Index:* Human ($0.710$) hoards far more than Cooperator ($0.116$), Tit-for-Tat ($0.298$), Random ($0.018$), and Free-Rider ($0.392$).
  - *Society Gini:* Random ($0.217$) and Human ($0.199$) create the highest disparity.
  - *Alliance Count:* Cooperator ($6.47$), Tit-for-Tat ($1.47$), Human ($0.00$ in single-round sessions).

#### 🛡️ Paper Figure 4: Retained-Wealth Index & Focal Survival Distributions (Page 4)
* Left: Boxplots of retained wealth per group showing real humans clustered tightly at the top ($0.71$).
* Right: Survival rate bar chart: Cooperator ($100\%$), Free-Rider ($100\%$), Real Human ($84\%$), Tit-for-Tat ($73\%$), Random ($13\%$).

#### 🎯 Paper Figure 5: Feature Ablation & 5-Fold Cross-Validated ROC Curves (Page 5)
* Left: Bar chart showing accuracy scaling from $89.3\%$ (Behavioral only) $\rightarrow$ $92.0\%$ (+ Deception) $\rightarrow$ $94.6\%$ (+ Latency) $\rightarrow$ **$97.3\%$** (+ Both) against the $53.6\%$ majority floor.
* Right: ROC curves for all four ablated feature sets, with the full feature model achieving $\text{AUC} = \mathbf{0.973}$.

#### ⚖️ Paper Figure 6: Logistic Weights & Drought Round-by-Round Action Mix (Page 5)
* Left: Standardized logistic regression weights ranking features: Retained Wealth ($+1.85$), Latency ($+1.22$), Deception ($+0.84$), Gini ($+0.52$), Gather ($+0.35$), Cooperation ($-0.48$), Alliance ($-1.15$).
* Right: Stacked bar chart of the action mix across drought rounds 1 to 5. Left bars (Human) are dominated by green (`gather`); right bars (AI) spread actions across orange (`share`) and blue (`communicate`).

---

### PART C: The Live Researcher Portal Interactive Charts (`researcher_hub.py`)

#### 1. Portal Tab 1: Scenarios Distribution Chart (`fig_sc`)
* **Chart Type:** Vertical bar chart (`go.Bar`).
* **Visual Mapping:** X-axis shows scenario conditions (*Calm Baseline*, *Drought Scarcity*, *Repeated-Trust*); Y-axis shows trial counts ($N$). Bar color: `#4f9ae0`.
* **Utility:** Verifies cohort sample balance across experimental conditions.

#### 2. Portal Tab 1: Behavioral Action Profile (`fig_act`)
* **Chart Type:** Grouped bar chart comparing Human (Navy `#4f9ae0`) vs. AI Agent (Orange `#e0762a`).
* **Visual Mapping:** X-axis lists the 5 action primitives: *Gather*, *Share*, *Hoard*, *Communicate*, *Deception*. Y-axis shows allocation percentage ($0\% - 100\%$).
* **Utility:** Instantly reveals the behavioral divide: human gathering and hoarding dominance vs. AI unhedged sharing.

#### 3. Portal Tab 1: Mean Cognitive Latency by Scenario (`fig_lat`)
* **Chart Type:** Bar chart displaying average human decision latency in milliseconds across Calm, Drought, and Trust.
* **Visual Mapping:** Displays exact text labels (e.g., `2450 ms`, `9119 ms`) directly above each bar.
* **Utility:** Highlights the cognitive hesitation induced by resource shock.

#### 4. Portal Tab 1: Commons Depletion Trajectory (`pivot_r`)
* **Chart Type:** Interactive line chart.
* **Visual Mapping:** X-axis shows Rounds 1 to 10; Y-axis shows mean lake water reserves ($0 - 50$ units).
* **Utility:** Traces the physical collapse of the shared lake pool following the Round 6 drought shock.

#### 5. Portal Tab 1: Society Wealth Inequality Gini Comparison (`fig_gini`)
* **Chart Type:** Grouped bar chart comparing Society Gini coefficient ($0.0 - 1.0$) for Human vs. AI across scenarios.
* **Utility:** Demonstrates that human social dynamics consistently generate higher wealth inequality through selective reciprocity.

#### 6. Portal Tab 2: Live Multi-LLM Diagnostic Ping Round-Trip Latency (`chart_data`)
* **Chart Type:** Real-time horizontal/vertical latency bar chart.
* **Visual Mapping:** Shows millisecond round-trip response times for Groq LPU, Google Gemini TPU, OpenRouter, and local Ollama.
* **Utility:** Allows researchers to verify API responsiveness and benchmark provider speeds live.

#### 7. Portal Tab 2: Human Decision Latency Distribution Histogram (`fig_h_lat`)
* **Chart Type:** 20-bin histogram (`px.histogram`) color-coded by scenario.
* **Visual Mapping:** X-axis shows decision latency in milliseconds; Y-axis shows action counts.
* **Utility:** Shows the right-skewed distribution of human deliberation times, contrasting with AI's deterministic $0\text{ ms}$ execution.

#### 8. Portal Tab 2: Cooperation vs. Hoarding Dynamics (`fig_social`)
* **Chart Type:** Grouped bar chart breaking down Share % (Blue) vs. Hoard % (Orange) across all 5 agent policies (`human`, `cooperator`, `free_rider`, `tit_for_tat`, `random`).
* **Utility:** Directly illustrates that the human policy balances self-preservation hoarding against social cooperation.

#### 9. Portal Tab 2: Scarcity Survival Resilience by Policy (`fig_surv`)
* **Chart Type:** Bar chart showing the percentage of rounds where agents successfully maintained water reserves above the survival threshold ($> 0$).
* **Utility:** Benchmarks policy resilience under extreme resource constraints.

#### 10. Portal Tab 5: Human Decision Step Counts for Imitation Learning (`fig_acts`)
* **Chart Type:** Bar chart showing action frequencies across the $322$ human decision steps: Gather ($225$), Share ($67$), Hoard ($13$), Communicate ($15$), Skip ($2$).
* **Utility:** Visualizes the training distribution used to fit the Human Behavioral Clone Policy.

#### 11. Portal Tab 6: Real-Time Softmax Forward Inference Probability Chart (`fig_prob`)
* **Chart Type:** Dynamic Plotly bar chart updated live as researchers adjust the Round, Reserve, Drought, and Severity sliders.
* **Visual Mapping:** Displays predicted probabilities ($0\% - 100\%$) across all 5 actions.
* **Utility:** Demonstrates real-time AI steering and counterfactual simulation.

---


## 6. The 7 Researcher Portal Tabs (`researcher_hub.py`)

The researcher portal is accessed at `localhost:8501` (authenticated with `admin` / `scarcity2026`).

| Tab | Name | Capabilities & Research Utility |
|:---:|---|---|
| **Tab 1** | **📊 Study Telemetry** | Unblinded trial counts, scenario distributions, action breakdown percentages (Gather/Share/Hoard/Communicate), round-by-round lake depletion trajectories, and live Gini wealth inequality graphs. |
| **Tab 2** | **⚡ API Operations & In-Game Performance** | Multi-tier key pool health (Groq LPU, Gemini TPU, OpenRouter, Ollama); live 1-token latency ping diagnostic; rate limit optimizations (LRU cache, key pooling); and empirical in-game policy performance. |
| **Tab 3** | **📐 Hypothesis Tests & Slopes** | Interactive statistical filtering across Calm, Drought, and Trust conditions; two-sided Mann-Whitney $U$, Cliff's $\delta$, Cohen's $d$; and N1 Dose-Response Elasticity slopes. |
| **Tab 4** | **🖼️ Publication Figures (300 DPI)** | Full suite of 8 publication-ready 300 DPI figures with dedicated scientific reading guides. |
| **Tab 5** | **🧠 Model Training Center** | One-click retraining of the Distinguishability Classifier (Model 1) and Human Behavior Clone Policy (Model 2) directly on banked SQLite data. |
| **Tab 6** | **🔮 Interactive Behavior Simulator** | Live forward inference sandbox allowing users to adjust Round, Water Reserves, Drought, and Severity sliders to predict human action probabilities in real time. |
| **Tab 7** | **🗄️ Relational Data Explorer** | Direct SQLite table browser (`trials`, `actions`) with round-by-round event drilldown and instant exports (CSV, SQLite DB, LLM SFT JSONL). |

---

## 7. Viva Defense Master Plan: Examiner Questions & Bulletproof Answers

### 🎤 1-Minute Pitch
> *"Respected examiners, our study investigates a fundamental AI safety question: **When shared resources run out, do AI agents behave like humans?** Using a 5-player Common Pool Resource simulation based on Elinor Ostrom's economic theory, we implemented a focal-player substitution protocol across 112 validated trials, holding companion policies fixed while alternating human participants with AI agents. We found that humans exhibit marked behavioral divergence under drought: cooperation collapses to 4.4%, defensive wealth retention surges to 71%, and 14.3% to 27.3% of human claims are strategically deceptive. In contrast, AI baselines maintain rigid, unhedged routines with 0% deception. We trained a classifier that separates human from AI trajectories with 97.3% cross-validated accuracy. This proves that current AI agents do not naturally reproduce human crisis dynamics, providing vital empirical data for governing multi-agent autonomous systems."*

---

### ❓ Top 10 Technical Viva Questions

#### Q1: "Why did you use Elinor Ostrom's Common Pool Resource model instead of standard Prisoner's Dilemma?"
**Answer:**  
*"The Prisoner's Dilemma is a static, 2-player dyadic game with binary payoffs and no depletable resource dynamics. Ostrom's CPR framework models real-world shared infrastructure: 5 agents, finite carrying capacity ($K=100$), logistic regeneration ($r=0.4$), and collective over-extraction penalties. If agents over-gather, the commons collapses permanently, creating realistic existential survival pressure."*

#### Q2: "What is your Focal-Player Substitution design and why was it necessary?"
**Answer:**  
*"In unstructured multi-agent setups, if you place an LLM with humans, differences cannot be cleanly attributed to the model because human actions contaminate the state. Our protocol freezes four companion policies (Cooperator, Free-Rider, Tit-for-Tat, Random) across matched random seeds ($0 \dots 29$), swapping only the 5th focal seat. This ensures that any observed variance in cooperation, hoarding, or survival is strictly attributable to the focal decision-maker."*

#### Q3: "Why did real humans cooperate less than AI baselines (0.044 vs. 0.158)?"
**Answer:**  
*"Under severe drought ($\sigma = 0.7$), the sustainable yield drops to 3 units/round while the 5 agents require 10 units. Sharing under these conditions is suicidal without guaranteed reciprocity. Furthermore, 30 of our 37 real human sessions were single-round, where participants correctly recognized that one-shot sharing cannot establish multi-round reciprocity. Hence, humans rationally prioritized self-preservation."*

#### Q4: "How is deception defined and measured in your study?"
**Answer:**  
*"We eliminated subjective LLM evaluation by using machine-verifiable slotted messages: $\langle \text{kind}, \text{value}, \text{target}, \text{surface} \rangle$. When an agent communicates a `claimed_stock` of $X$, our pipeline checks the ground truth:
$$\text{Deception} = \mathbb{I}(\text{Claimed Stock} \neq \text{Resource Before})$$
Humans made false claims in $14.3\%$ of pooled messages and $27.3\%$ of drought messages (e.g., claiming 1 unit while holding 5 to deter requests). AI baselines made 0 claims."*

#### Q5: "Your classifier reached 97.3% accuracy. What were the most important features?"
**Answer:**  
*"As shown in Table VII and Figure 6, behavioral features alone achieved 89.3% accuracy (0.906 AUC). The single strongest predictor of human origin was the **Retained Wealth Index** (weight $+1.85$), followed by **Decision Latency** ($+1.22$) and **Deception Rate** ($+0.84$). The strongest predictor of AI origin was **Alliance Count** ($-1.15$), because AI policies execute mechanical reciprocity that humans do not display in crisis."*

#### Q6: "Why is decision latency treated as a structural cue rather than pure deliberation?"
**Answer:**  
*"Human participants take time to read the UI, deliberate, and decide (median 231 ms overall, spiking to 9,119 ms in complex moral dilemmas). Scripted AI baselines execute in 0 ms. Therefore, while latency correlates with human moral hesitation, we report classifier results both with and without latency (89.3% vs. 97.3%) to ensure our findings do not depend on timing artifacts."*

#### Q7: "What is the qualitative 'Altruistic Martyr' case (`drought_human_003`)?"
**Answer:**  
*"In session `drought_human_003`, participant `PAB87` hoarded once in round 2, but then gave away their remaining water during rounds 3–5 to keep co-players alive, dehydrating to death in round 5. Their decision latency dropped from 9.1 s in round 1 to 2.3 s as they committed to sacrifice. Standard utility-maximizing RL and scripted bots never display suicidal altruism."*

#### Q8: "What are the limitations of your study?"
**Answer:**  
*"We clearly acknowledge seven limitations:
1. The analyzed AI arm consists of 60 scripted trials; the 959-trial RL/LLM campaign was frozen separately.
2. Real human trials were conducted in drought, and 30 were single-round.
3. 15 human proxy trials are script-generated (reported separately).
4. Classifier accuracy partially leverages latency and deception.
5. Narrow demographic (KIET undergraduate students, age 18–24).
6. Deception covers false stock claims only, not broken promises.
7. Web modality differs from AI prompt execution."*

#### Q9: "How does your multi-tier API infrastructure prevent crashes during high traffic?"
**Answer:**  
*"We implemented a 4-tier resilient cascade: `Groq LPU` $\rightarrow$ `OpenRouter` $\rightarrow$ `Google Gemini` $\rightarrow$ `Local Ollama (Llama-3.2)`. When cloud rate limits (HTTP 429) occur, the system fails over automatically to local Ollama, which has 0 cost and no rate limits. In our 959-trial campaign, 234 LLM calls completed with 0 dropped trials and 0 parse errors."*

#### Q10: "What is the ultimate real-world takeaway for AI Safety?"
**Answer:**  
*"Assuming autonomous AI agents deployed in shared infrastructures (power grids, water allocation, disaster relief) will behave like humans during crises is dangerous. In crisis, humans protect private reserves, deliberate morally, and engage in strategic communication. AI agents trained on reward maximization or static text will either naively deplete the commons or act with mechanical rigidity. Safe multi-agent governance requires empirical behavioral validation against ground truth."*
