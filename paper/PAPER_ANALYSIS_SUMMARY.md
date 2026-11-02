# 📄 Complete Manuscript Analysis: Behavioral Divergence Under Resource Scarcity

**Conference / Manuscript Draft:** *Behavioral Divergence Between LLM-Driven Multi-Agent Societies and Humans Under Resource Scarcity*  
**Authors:** Utkarsh Pandey$^1$, Saksham Singh$^2$, Sujal Kumar$^3$, Yashash Tyagi$^4$, Laxmi$^5$ (Mentor)  
**Affiliation:** Department of Computer Science & Engineering (AI & ML), Krishna Institute of Engineering & Technology (KIET), Ghaziabad, Delhi-NCR, India  
**Emails:** `{utkarshpandey.up.2004, saksham.singh2395, sujalkumar2511, yashashtyagi, laxchauhan98}@gmail.com`

---

## 1. Research Questions & Hypotheses

### Research Questions
- **RQ1:** How do human and AI focal players differ in cooperation, hoarding, and fairness under scarcity?
- **RQ2:** How often do humans deceive when the common pool collapses?
- **RQ3:** Can human and AI players be told apart from behavior alone?

### Accompanying Hypotheses
- **H1:** Relative to rule-based baselines, humans hoard more and cooperate selectively.
- **H2:** Humans tolerate and generate more resource inequality (higher Society Gini).
- **H3:** Humans sometimes misreport their private resource stock under scarcity shock.
- **H4:** Humans are separable from baselines well above the majority-class rate using behavioral classifiers.

---

## 2. Experimental Environment: `ScarcityEnv` Mathematical Model

### Dynamic Commons Formulation
- 5 agents share a central freshwater lake.
- Carrying capacity $K = 100.0$, intrinsic regeneration $r = 0.40$:
  $$S_{t+1} = S_t + r S_t \left(1 - \frac{S_t}{K}\right) - D_t$$
- Proportional harvest scaling when total demand $D_t > S_t$:
  $$Y_i = D_i \cdot \frac{S_t}{D_t}$$
- Survival fee: 2 water units per agent per round. Reserve $< 0 \rightarrow$ elimination.
- Sustainable yield: $\text{MSY} = \frac{r(1-\sigma)K}{4}$. At $\sigma=0.7$, $\text{MSY} = 3.0$ units/round (society requires 10 units/round).

### Machine-Verifiable Deception
$$\text{Deception} = \mathbb{I}(\text{Claimed Stock} \neq \text{Resource Before})$$
Scored on structured message kinds: `claim_stock`, `promise_share`, `request`, `accuse`.

---

## 3. Manuscript Tables & Empirical Data

### Table I: Literature Review Comparison Matrix
| Reference | Focus / Method | Key Findings | Limitations / Gap Relative to This Work |
|---|---|---|---|
| **Park et al., 2023** | Generative agents in "Smallville" | Believable emergent social routines | No scarcity or survival pressure; no human baseline |
| **Lowe et al., 2017** | MADDPG multi-agent actor-critic | Mixed cooperative-competitive strategies | Numeric policies only, no language/communication; no human comparison |
| **Akata et al., 2023** | Repeated economic matrix games | LLMs approximate rational strategies | Single-agent evaluation; no shared depletable resource |
| **Niszczota et al., 2025** | Prisoner's Dilemma with LLM bots | Humans cooperate 10-15% less with LLMs | 2-player dyadic game; no multi-agent commons; no verifiable deception |
| **Liang et al., 2025** | MAC-SPGG public goods game | Stable cooperative equilibria in LLMs | Focus on LLM ensemble performance, no human comparison or survival stakes |
| **Chen et al., 2025** | Survival Games (2 humans + 1 LLM) | Model families differ in selfishness | Shared unstructured narrative without fixed controls or distinguishability metric |
| **Mohamadi & Yavari, 2025** | DECIDE-SIM (11 LLMs in survival) | Scarcity increases unethical behavior | 100% AI, zero human participants; cannot evaluate human-likeness |
| **Mullainathan & Shafir, 2013** | Behavioral economics of scarcity | Scarcity captures attention, narrows honesty | Human-only; no computational agents or multi-agent commons |

---

### Table II: Experimental Scenarios
| Scenario | Rounds | Matched Seeds | Perturbation |
|---|:---:|:---:|---|
| **Calm** | 10 | 0–29 | None ($\sigma = 0.0$) |
| **Drought** | 10 | 0–29 | Round-6 shock: yield $3 \rightarrow 1$, regeneration $\times 0.3$ ($\sigma = 0.7$) |
| **Repeated-Trust** | 30 | 0–29 | Long horizon testing sustained multi-round reciprocity |

---

### Table III: Operational Definitions of Behavioral Features
- **Cooperation Rate:** $(\text{shares} + \text{communicate actions}) / \text{rounds}$
- **Retained Wealth Index:** $\text{final resource} / \text{total available}$ (the "hoarding index")
- **Gather Rate:** fraction of rounds with a `gather` action
- **Society Gini:** $G = \frac{\sum_i \sum_j |x_i - x_j|}{2 n^2 \bar{x}}$ ($n=5$)
- **Alliances:** count of reciprocal sharing pairs
- **Deception Rate:** $\text{false stock claims} / \text{stock claims}$
- **Latency:** mean decision response time in milliseconds

---

### Table IV: Composition of the 112 Analyzed Trials
| Arm | Subset | Trials |
|---|---|:---:|
| **Human** | Real, single-round (drought) | 30 |
| **Human** | Real, multi-round (drought) | 7 |
| **Human** | Scripted proxy (calm, drought, trust) | 15 |
| **AI** | Cooperator / Tit-for-Tat / Random / Free-Rider (15 each) | 60 |
| **Total** | | **112** |

*(Note: A separate 959-trial RL/hybrid/LLM campaign was frozen with 0 rate-limited calls and 0 parse errors across 234 LLM calls).*

---

### Table V: Real Human Sessions ($n=37$) vs. Pooled AI Baselines ($n=60$)
| Metric | Human | AI | Cliff's $\delta$ | Mann-Whitney $p$ |
|---|:---:|:---:|:---:|:---:|
| **Cooperation Rate** | $0.044$ | $0.158$ | **$-0.53$** | $3 \times 10^{-6}$ |
| **Gather Rate** | $0.884$ | $0.662$ | **$+0.58$** | $8 \times 10^{-7}$ |
| **Retained Wealth** | $0.710$ | $0.206$ | **$+0.71$** | $2 \times 10^{-9}$ |
| **Society Gini** | $0.199$ | $0.108$ | **$+0.43$** | $2 \times 10^{-4}$ |
| **Alliances** | $0.00$ | $2.15$ | **$-0.57$** | $4 \times 10^{-8}$ |

---

### Table VI: Per-Policy AI Baselines vs. Real Human Sessions
| Focal Policy | Cooperation Rate | Retained Wealth | Society Gini | Alliances | Survival Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Cooperator** | $0.371$ | $0.116$ | $0.163$ | $6.47$ | $1.00$ |
| **Tit-for-Tat** | $0.109$ | $0.298$ | $0.053$ | $1.47$ | $0.73$ |
| **Random** | $0.152$ | $0.018$ | $0.217$ | $0.67$ | $0.13$ |
| **Free-Rider** | $0.000$ | $0.392$ | $0.000$ | $0.00$ | $1.00$ |
| **Real Human ($n=37$)** | **$0.044$** | **$0.710$** | **$0.199$** | **$0.00$** | **$0.84$** |

---

### Table VII: Classifier Ablation (112 Trials, Stratified 5-Fold CV)
| Feature Set | 5-Fold CV Accuracy | ROC-AUC Score |
|---|:---:|:---:|
| **Behavioral Only** | $0.893$ ($89.3\%$) | $0.906$ |
| **+ Deception** | $0.920$ ($92.0\%$) | $0.957$ |
| **+ Latency** | $0.946$ ($94.6\%$) | $0.933$ |
| **+ Deception + Latency (Full)** | **$0.973$ ($97.3\%$)** | **$0.973$** |
| **Majority Class Floor** | $0.536$ ($53.6\%$) | $0.500$ |

*Ablation Without Proxy Trials ($n=97$ trials, 61.9% floor):* Behavioral alone achieves **93.7% accuracy (0.918 AUC)**; with deception + latency achieves **96.9% accuracy (0.978 AUC)**.

---

## 4. Key Takeaways for Publication & Defense

1. **Strategic Deception (RQ2):** 14.3% of pooled human stock claims (3 of 21) were false, rising to 27.3% (3 of 11) under drought. Scripted AI baselines produced 0 claims (0% deception).
2. **Behavioral Distinguishability (RQ3):** Behavioral features alone cleanly separate humans from AI ($89.3\% - 93.7\%$), driven primarily by the Retained Wealth Index ($+1.85$ weight) and Alliance Count ($-1.15$ weight).
3. **Behavioral Cloning (Model B):** Softmax policy fitted to human logs reaches $75.4\%$ action agreement on 321 decision steps, providing an empirical baseline for steerable human-aligned agents.
4. **Ostrom Commons Reality:** Without centralized governance or guaranteed reciprocity, human societies faced with severe resource deficits experience rapid cooperation collapse and defensive wealth retention.
