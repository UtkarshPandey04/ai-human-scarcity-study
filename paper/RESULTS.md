# Section V: Empirical Results & Comparative Analysis

**Paper:** *Behavioral Divergence Between LLM-Driven Multi-Agent Societies and Humans Under Resource Scarcity*  
**Authors:** Ms. Laxmi (Mentor), Utkarsh Pandey, Sujal Kumar, Saksham Singh, Yashash Tyagi  
**Institution:** Dept. of Computer Science & Engineering (AI & ML), KIET Deemed to be University, Ghaziabad, India  

---

## 1. Overview of Experimental Campaign

To empirically answer whether autonomous AI agents diverge from human behavior under resource scarcity, we executed a matched-seed experimental campaign across three canonical environmental regimes:
1. **Calm Baseline Condition** ($N=25$ trials; 5 Human, 20 AI; 10 rounds; abundance regeneration).
2. **Drought Scarcity Shock** ($N=34$ trials; 14 Human, 20 AI; 10 rounds; Round 6 resource production suppressed by 70%, continuous severity sweep $\sigma \in \{0.0, 0.5, 0.7\}$).
3. **Repeated-Trust Condition** ($N=25$ trials; 5 Human, 20 AI; 30 rounds; sustained depletable pool demanding multi-round reciprocity).

All trials followed **focal-player substitution** (holding co-players $A_2$–$A_5$ fixed across identical random seeds while substituting only the focal seat $A_1$ between human participants and AI agents). In total, **84 trials** containing **5,320 individual decision events** were logged, verified against all game invariants with a 100% QA pass rate, and synchronized to the relational research database.

---

## 2. Statistical Divergence Across Behavioral Metrics

Because behavioral counts and action frequencies exhibit non-normality, we conducted two-sided **Mann-Whitney $U$ tests** alongside non-parametric effect sizes (**Cliff’s Delta** $\delta$) and parametric effect sizes (**Cohen’s $d$**). Table 1 reports the pooled and scenario-stratified comparisons.

### Table 1: Empirical Behavioral Divergence (Human vs. AI Focal Agents)

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney $U$ | $p$-value | Cliff's $\delta$ | Effect Magnitude | Cohen's $d$ |
|:-------|:---------------:|:------------:|:----------------:|:---------:|:----------------:|:----------------:|:-----------:|
| **All Scenarios (Pooled)** | | | | | | | |
| Cooperation Rate | 0.251 (0.13) | 0.158 (0.05) | 963.0 | **0.0151\*** | +0.338 | Medium | +0.94 |
| Total Water Shared | 8.125 (9.73) | 5.633 (3.63) | 936.0 | **0.0306\*** | +0.300 | Small | +0.35 |
| Society Gini Index | 0.266 (0.17) | 0.108 (0.05) | 972.5 | **0.0096\*\*** | +0.351 | Medium | +1.26 |
| Deception Rate | 0.125 (0.34) | 0.000 (0.00) | 810.0 | **0.0058\*\*** | +0.125 | Negligible | +0.52 |
| Decision Latency (ms) | 1,759 (1,048) | 0.0 (0.0) | 1,200.0 | **0.0000\*\*\*** | +0.667 | Large | +2.37 |
| **Drought Condition (Scarcity)** | | | | | | | |
| Hoarding Rate | 0.138 (0.10) | 0.046 (0.04) | 215.5 | **0.0037\*\*** | **+0.539** | **Large** | **+1.20** |
| Deception Rate | 0.214 (0.42) | 0.000 (0.00) | 170.0 | **0.0357\*** | **+0.214** | **Small** | **+0.72** |
| Society Survival Rate | 0.611 (0.40) | 1.000 (0.00) | 70.0 | **0.0006\*\*\*** | **-0.500** | **Large** | **-1.37** |
| Alliance Count | 0.286 (0.47) | 1.400 (0.50) | 87.5 | **0.0403\*** | **-0.375** | **Medium** | **-2.28** |
| **Repeated-Trust Condition** | | | | | | | |
| Society Gini Index | 0.453 (0.07) | 0.053 (0.03) | 100.0 | **0.0002\*\*\*** | **+1.000** | **Large** | **+7.42** |
| Hoarding Index | 0.075 (0.03) | 0.017 (0.01) | 93.0 | **0.0030\*\*** | **+0.860** | **Large** | **+2.60** |
| Total Water Shared | 23.60 (10.9) | 9.55 (2.95) | 74.0 | 0.1060 | +0.480 | Large | +1.77 |

*Significance: $^\ast p < 0.05$, $^{\ast\ast} p < 0.01$, $^{\ast\ast\ast} p < 0.001$. Two-sided Mann-Whitney $U$ test.*

---

## 3. Novelty N1: Scarcity Dose-Response Elasticity Curves

Rather than evaluating scarcity as a binary on/off state, we characterized the behavioral response slope across scarcity intensities $\sigma \in [0.0, 0.7]$.

$$\text{Elasticity of Sharing} = \frac{\partial \text{Share}}{\partial \sigma}, \quad \text{Elasticity of Hoarding} = \frac{\partial \text{Hoard}}{\partial \sigma}$$

- **Human Cooperation Collapse:**  
  $$\frac{\partial \text{Share}_{\text{Human}}}{\partial \sigma} = -0.1559, \quad \frac{\partial \text{Share}_{\text{AI}}}{\partial \sigma} = -0.0072$$  
  Human sharing drops precipitously under intensifying scarcity ($-15.6\%$ reduction per unit severity), whereas AI sharing remains virtually flat ($-0.7\%$), showing that AI agents fail to reproduce the non-linear psychological collapse of human cooperation under stress.

- **Human Defensive Hoarding Surge:**  
  $$\frac{\partial \text{Hoard}_{\text{Human}}}{\partial \sigma} = +0.1942, \quad \frac{\partial \text{Hoard}_{\text{AI}}}{\partial \sigma} = -0.0959$$  
  While human hoarding surges by $+19.4\%$ as environmental stress increases, AI agents exhibit reflexive algorithmic gathering that decreases hoarding in favor of short-term pool draws.

*(See Figure 2 in `paper/figures/fig2_dose_response.png`).*

---

## 4. Novelty N2: Machine-Verifiable Arithmetic Deception

Through our structured slotted messaging schema, deception is verified as an arithmetic mismatch:

$$\text{Deception} = \mathbb{I}(\text{Claimed Stock} \neq \text{Ground-Truth Resource Before})$$

In the Drought condition, **21.4% of human stock claims were arithmetically false** ($p = 0.0357$), where participants systematically understated their reserves (e.g., reporting 1 or 2 units when holding 4 to 6 units) to discourage extraction by co-players. In contrast, unprompted AI agents exhibited **0.0% deception**, acting with strict literal compliance.

---

## 5. Novelty N3: Distinguishability Classification & Attributions

We evaluated whether a machine learning classifier can distinguish an AI-driven trajectory from a human trajectory based strictly on behavioral feature vectors:

### Table 2: AI-vs-Human Distinguishability Performance (Stratified 5-Fold CV)

| Scenario / Condition | Logistic Regression AUC | Logistic Accuracy | Random Forest AUC | Random Forest Accuracy | F1-Score |
|:---------------------|:-----------------------:|:-----------------:|:-----------------:|:----------------------:|:--------:|
| **All Scenarios (Overall)** | **0.897** | **86.9%** | **0.940** | **91.7%** | **0.837** |
| Calm Baseline ($\sigma=0.0$) | 1.000 | 96.0% | 1.000 | 96.0% | 0.909 |
| Drought Scarcity ($\sigma=0.7$) | 0.879 | 82.4% | 0.921 | 85.3% | 0.769 |
| Repeated-Trust | 1.000 | 100.0% | 1.000 | 96.0% | 0.909 |

### Feature Importance & Behavioral Drivers
Permutation importance on the Random Forest ensemble identified the top behavioral drivers separating humans from AI agents:
1. **Society Gini Index** (Permutation Importance: `0.1821`): Humans generate dramatic wealth inequality through selective sharing, whereas AI populations maintain an artificial egalitarian uniformity.
2. **Cooperation Rate** (Weight: `+1.7307` [More Human]): Humans engage in rich bidirectional communication and targeted altruism.
3. **Alliance Count** (Weight: `-1.5690` [More AI]): AI agents exhibit rigid, mechanical reciprocity with scripted tit-for-tat agents.
4. **Hoarding Index** (Weight: `+1.5219` [More Human]): Humans retain defensive surplus under existential risk.
5. **Arithmetic Deception Rate** (Weight: `+0.8371` [More Human]): Strategic false signaling is uniquely human.

*(See Figure 3 & Figure 4 in `paper/figures/`).*

---

## 6. Qualitative Insights: Martyrs, Defectors, and Automatons

Qualitative inspection of transcripts (`paper/QUALITATIVE_FINDINGS.md`) illustrates the cognitive divergence:
- **Human Self-Sacrifice:** In trial `drought_human_003_e49479`, participant `PAB87` continued sharing 1 unit of water with co-players across rounds 3, 4, and 5 despite holding only 1 unit of reserve, ultimately dying in round 5 to sustain the group.
- **AI Policy Invariance:** In identical matched seeds, AI agent `A1` never accepted self-sacrifice, prioritizing monotonic survival functions.
- **Deliberation Latency:** Human mean latency reached $2{,}450$ ms in calm and up to $9{,}119$ ms during drought transitions, reflecting intense moral deliberation absent in instantaneous AI execution.

---

## 7. Camera-Ready Figures Generated

The following 300 DPI publication figures are ready for inclusion:
- `paper/figures/fig1_behavioral_comparison.png` — Multi-metric distributions across scenarios.
- `paper/figures/fig2_dose_response.png` — Scarcity dose-response slopes for sharing and hoarding.
- `paper/figures/fig3_distinguishability_roc.png` — ROC-AUC distinguishability scores across scenarios.
- `paper/figures/fig4_feature_importance.png` — Permutation importance and logistic regression weights.
