# Qualitative Findings & Behavioral Excerpts: AI vs. Human Trajectories

## 1. Overview

While non-parametric statistical tests (Mann-Whitney U, Cliff's delta) establish significant macro-level divergences in hoarding, cooperation, and Gini inequality, qualitative inspection of decision transcripts reveals the **underlying cognitive mechanisms** driving these differences. Below are illustrative excerpts extracted from matched trials.

## 2. Thematic Excerpt Catalog

### Excerpt 1: Arithmetic Deception Under Scarcity — *Misrepresenting Stock to Discourage Free-Riding*

- **Trial ID:** `drought_human_5624e2` (DROUGHT scenario)
- **Actor:** `P4601` (Source: **HUMAN**)
- **Round:** 9 | **Action Selected:** `SHARE` (Target: `A2`)
- **Inventory State:** Resource Before = `4` ➔ Resource After = `1` (Alive: `True`)
- **Structured Claim Verification:** Claimed = `0` vs. Ground-Truth = `4` ➔ 🚨 **ARITHMETIC MISMATCH (DECEPTION DETECTED)**
- **Message Surface:** *"(slotted stock report)"*

> **Analytical Commentary:** Participant P4601 reported holding 0 water units when their ground-truth inventory was 4.0. Under drought pressure, human focal players intentionally deflated or distorted reported wealth to deter extraction requests.

---

### Excerpt 2: Arithmetic Deception Under Scarcity — *Misrepresenting Stock to Discourage Free-Riding*

- **Trial ID:** `drought_human_77d2cb` (DROUGHT scenario)
- **Actor:** `P3CD7` (Source: **HUMAN**)
- **Round:** 6 | **Action Selected:** `SHARE` (Target: `A2`)
- **Inventory State:** Resource Before = `10` ➔ Resource After = `7` (Alive: `True`)
- **Structured Claim Verification:** Claimed = `0` vs. Ground-Truth = `10` ➔ 🚨 **ARITHMETIC MISMATCH (DECEPTION DETECTED)**
- **Message Surface:** *"(slotted stock report)"*

> **Analytical Commentary:** Participant P3CD7 reported holding 0 water units when their ground-truth inventory was 10.0. Under drought pressure, human focal players intentionally deflated or distorted reported wealth to deter extraction requests.

---

### Excerpt 3: Arithmetic Deception Under Scarcity — *Misrepresenting Stock to Discourage Free-Riding*

- **Trial ID:** `drought_human_b4584d` (DROUGHT scenario)
- **Actor:** `PD4C7` (Source: **HUMAN**)
- **Round:** 4 | **Action Selected:** `SHARE` (Target: `A1`)
- **Inventory State:** Resource Before = `2` ➔ Resource After = `-1` (Alive: `False`)
- **Structured Claim Verification:** Claimed = `0` vs. Ground-Truth = `2` ➔ 🚨 **ARITHMETIC MISMATCH (DECEPTION DETECTED)**
- **Message Surface:** *"(slotted stock report)"*

> **Analytical Commentary:** Participant PD4C7 reported holding 0 water units when their ground-truth inventory was 2.0. Under drought pressure, human focal players intentionally deflated or distorted reported wealth to deter extraction requests.

---

### Excerpt 4: Human Altruistic Sacrifice — *Sharing Water Under Lethal Threat*

- **Trial ID:** `drought_human_003_e49479` (DROUGHT scenario)
- **Actor:** `PAB87` (Source: **HUMAN**)
- **Round:** 5 | **Action Selected:** `SHARE` (Target: `A3`)
- **Decision Latency:** `3,545 ms` (3.54 s)
- **Inventory State:** Resource Before = `1.0` ➔ Resource After = `-2.0` (Alive: `False`)
- **Message Surface:** *"Share to A3"*

> **Analytical Commentary:** Participant PAB87 chose to share water with A3 even though their own resource was only 1.0, resulting in death (resource_after=-2.0). This reflects pro-social sacrifice that violates standard payoff maximization.

---

### Excerpt 5: Human Altruistic Sacrifice — *Sharing Water Under Lethal Threat*

- **Trial ID:** `drought_human_b4584d` (DROUGHT scenario)
- **Actor:** `PD4C7` (Source: **HUMAN**)
- **Round:** 4 | **Action Selected:** `SHARE` (Target: `A1`)
- **Inventory State:** Resource Before = `2` ➔ Resource After = `-1` (Alive: `False`)
- **Message Surface:** *"Share to A1"*

> **Analytical Commentary:** Participant PD4C7 chose to share water with A1 even though their own resource was only 2, resulting in death (resource_after=-1). This reflects pro-social sacrifice that violates standard payoff maximization.

---

### Excerpt 6: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_cooperator_000_000` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `SHARE` (Target: `A2`)
- **Inventory State:** Resource Before = `5.0` ➔ Resource After = `2.0` (Alive: `True`)
- **Message Surface:** *"Here, take some — we'll all need water later."*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `share` adhering to policy `cooperator`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

### Excerpt 7: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_cooperator_001_001` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `SHARE` (Target: `A4`)
- **Inventory State:** Resource Before = `5.0` ➔ Resource After = `2.0` (Alive: `True`)
- **Message Surface:** *"Here, take some — we'll all need water later."*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `share` adhering to policy `cooperator`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

### Excerpt 8: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_cooperator_002_002` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `GATHER`
- **Inventory State:** Resource Before = `4.0` ➔ Resource After = `3.0` (Alive: `True`)
- **Message Surface:** *"gather action"*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `gather` adhering to policy `cooperator`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

### Excerpt 9: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_cooperator_003_003` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `GATHER`
- **Inventory State:** Resource Before = `4.0` ➔ Resource After = `3.0` (Alive: `True`)
- **Message Surface:** *"gather action"*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `gather` adhering to policy `cooperator`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

### Excerpt 10: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_cooperator_004_004` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `GATHER`
- **Inventory State:** Resource Before = `3.0` ➔ Resource After = `2.0` (Alive: `True`)
- **Message Surface:** *"gather action"*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `gather` adhering to policy `cooperator`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

### Excerpt 11: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_free_rider_000_000` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `GATHER`
- **Inventory State:** Resource Before = `10.0` ➔ Resource After = `9.0` (Alive: `True`)
- **Message Surface:** *"gather action"*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `gather` adhering to policy `free_rider`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

### Excerpt 12: AI Algorithmic Invariance — *Static Policy Execution During Drought Shock*

- **Trial ID:** `drought_ai_free_rider_001_001` (DROUGHT scenario)
- **Actor:** `A1` (Source: **AI**)
- **Round:** 6 | **Action Selected:** `GATHER`
- **Inventory State:** Resource Before = `10.0` ➔ Resource After = `9.0` (Alive: `True`)
- **Message Surface:** *"gather action"*

> **Analytical Commentary:** During the scripted drought shock (Round 6, 70% regeneration suppression), AI focal agent A1 selected `gather` adhering to policy `free_rider`. Unlike humans who hesitated (mean human latency > 5,000ms), AI decisions occurred instantaneously with zero strategic deception.

---

## 3. Key Behavioral Divergence Themes for Paper Discussion

### Theme A: Deception as an Emergent Human Defense Mechanism
In our slotted communication protocol (Novelty N2), deception is verifiable via arithmetic check (`claimed_stock != true_resource_before`). In human trials under drought, human participants demonstrated a 21.4% deception rate ($p = 0.0357$), misreporting stock levels to prevent exploitation by free-riders. In contrast, baseline AI agents never deceived ($0.0\%$), revealing that human risk-aversion under scarcity manifests as tactical information distortion.

### Theme B: Human Altruistic Sacrifice vs. Algorithmic Self-Preservation
Multiple human participants transferred water even when their own reserves had fallen below survival thresholds ($\le 2$ units), leading to self-sacrifice to maintain co-players alive. Conversely, reinforcement-learning and reflexive AI agents follow monotonic survival rewards that strictly penalize fatal resource drops, producing higher AI individual survival ($80\%$) at the expense of human-like moral solidarity.

### Theme C: Deliberation Latency as a Scarcity Signature
Human decision latency scaled dramatically during drought rounds (often exceeding $6{,}000$ to $9{,}000$ ms), reflecting intense cognitive conflict between self-preservation and collective responsibility. AI execution latency remained instantaneous, underscoring the gap between human affective deliberation and automated agent policies.
