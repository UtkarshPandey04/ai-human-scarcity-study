# Empirical Statistical Findings: AI vs. Human Behavior Under Scarcity

This report presents the non-parametric hypothesis testing (Mann-Whitney U, Cliff's Delta) and parametric comparisons (Cohen's d, Welch's t-test) across all trials, verifying the behavioral divergence between humans and LLM-driven multi-agent societies.

### All Scenarios (Pooled)

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.094 (0.13) | 0.158 (0.15) | 1108.5 | 0.0059 ** | -0.289 (Small) | -0.46 |
| **Hoarding Rate** | 0.037 (0.08) | 0.090 (0.17) | 1393.5 | 0.2026  | -0.107 (Negligible) | -0.41 |
| **Hoarding Index** | 0.557 (0.37) | 0.206 (0.23) | 2425.0 | 0.0000 *** | +0.554 (Large) | +1.14 |
| **Gather Rate** | 0.823 (0.25) | 0.662 (0.28) | 2210.5 | 0.0001 *** | +0.417 (Medium) | +0.60 |
| **Cooperation Rate** | 0.116 (0.16) | 0.158 (0.15) | 1215.0 | 0.0354 * | -0.221 (Small) | -0.28 |
| **Deception Rate** | 0.058 (0.24) | 0.000 (0.00) | 1650.0 | 0.0619 † | +0.058 (Negligible) | +0.35 |
| **Total Water Shared** | 3.750 (7.02) | 5.633 (8.28) | 1188.0 | 0.0232 * | -0.238 (Small) | -0.25 |
| **Society Gini Coefficient** | 0.256 (0.14) | 0.108 (0.16) | 2400.5 | 0.0000 *** | +0.539 (Large) | +1.01 |
| **Society Survival Rate** | 0.891 (0.30) | 0.833 (0.38) | 1595.0 | 0.7522  | +0.022 (Negligible) | +0.17 |
| **Focal Survival** | 0.885 (0.32) | 0.717 (0.45) | 1822.0 | 0.0292 * | +0.168 (Small) | +0.43 |
| **Alliance Count** | 0.327 (0.68) | 2.150 (3.18) | 961.0 | 0.0001 *** | -0.384 (Medium) | -0.79 |
| **Decision Latency (ms)** | 1040.777 (1370.64) | 0.000 (0.00) | 2880.0 | 0.0000 *** | +0.846 (Large) | +1.07 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Calm Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.240 (0.05) | 0.170 (0.16) | 67.5 | 0.2388  | +0.350 (Medium) | +0.60 |
| **Hoarding Rate** | 0.000 (0.00) | 0.046 (0.11) | 40.0 | 0.3121  | -0.200 (Small) | -0.59 |
| **Hoarding Index** | 0.184 (0.06) | 0.307 (0.24) | 43.0 | 0.6564  | -0.140 (Negligible) | -0.69 |
| **Gather Rate** | 0.660 (0.05) | 0.696 (0.29) | 44.0 | 0.7021  | -0.120 (Negligible) | -0.17 |
| **Cooperation Rate** | 0.340 (0.05) | 0.170 (0.16) | 80.0 | 0.0406 * | +0.600 (Large) | +1.45 |
| **Deception Rate** | 0.000 (0.00) | 0.000 (0.00) | 50.0 | 1.0000  | +0.000 (Negligible) | +0.00 |
| **Total Water Shared** | 7.000 (1.41) | 3.850 (4.00) | 74.0 | 0.1055  | +0.480 (Large) | +1.05 |
| **Society Gini Coefficient** | 0.403 (0.05) | 0.148 (0.18) | 85.0 | 0.0182 * | +0.700 (Large) | +1.97 |
| **Society Survival Rate** | 0.960 (0.09) | 1.000 (0.00) | 40.0 | 0.0574 † | -0.200 (Small) | -0.63 |
| **Focal Survival** | 1.000 (0.00) | 0.800 (0.41) | 60.0 | 0.3098  | +0.200 (Small) | +0.69 |
| **Alliance Count** | 0.800 (0.84) | 1.800 (2.42) | 46.0 | 0.8012  | -0.080 (Negligible) | -0.55 |
| **Decision Latency (ms)** | 2450.000 (0.00) | 0.000 (0.00) | 100.0 | 0.0000 *** | +1.000 (Large) | +2450000000.00 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Drought Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.056 (0.12) | 0.155 (0.14) | 225.0 | 0.0009 *** | -0.464 (Medium) | -0.77 |
| **Hoarding Rate** | 0.046 (0.09) | 0.046 (0.11) | 439.5 | 0.7031  | +0.046 (Negligible) | +0.01 |
| **Hoarding Index** | 0.658 (0.33) | 0.294 (0.22) | 682.0 | 0.0000 *** | +0.624 (Large) | +1.29 |
| **Gather Rate** | 0.857 (0.27) | 0.711 (0.29) | 591.5 | 0.0040 ** | +0.408 (Medium) | +0.52 |
| **Cooperation Rate** | 0.067 (0.13) | 0.155 (0.14) | 246.5 | 0.0033 ** | -0.413 (Medium) | -0.65 |
| **Deception Rate** | 0.071 (0.26) | 0.000 (0.00) | 450.0 | 0.2321  | +0.071 (Negligible) | +0.39 |
| **Total Water Shared** | 1.000 (1.87) | 3.500 (3.49) | 233.0 | 0.0015 ** | -0.445 (Medium) | -0.89 |
| **Society Gini Coefficient** | 0.215 (0.12) | 0.124 (0.18) | 606.0 | 0.0031 ** | +0.443 (Medium) | +0.61 |
| **Society Survival Rate** | 0.870 (0.33) | 0.950 (0.22) | 372.0 | 0.2189  | -0.114 (Negligible) | -0.28 |
| **Focal Survival** | 0.857 (0.35) | 0.800 (0.41) | 444.0 | 0.5786  | +0.057 (Negligible) | +0.15 |
| **Alliance Count** | 0.095 (0.37) | 1.450 (1.93) | 193.0 | 0.0000 *** | -0.540 (Large) | -0.97 |
| **Decision Latency (ms)** | 705.248 (1318.02) | 0.000 (0.00) | 760.0 | 0.0000 *** | +0.810 (Large) | +0.76 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Repeated-Trust Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.267 (0.02) | 0.150 (0.16) | 71.5 | 0.1485  | +0.430 (Medium) | +1.05 |
| **Hoarding Rate** | 0.000 (0.00) | 0.180 (0.22) | 27.5 | 0.0803 † | -0.450 (Medium) | -1.14 |
| **Hoarding Index** | 0.075 (0.03) | 0.017 (0.02) | 93.0 | 0.0030 ** | +0.860 (Large) | +2.35 |
| **Gather Rate** | 0.700 (0.02) | 0.579 (0.25) | 75.5 | 0.0867 † | +0.510 (Large) | +0.67 |
| **Cooperation Rate** | 0.300 (0.02) | 0.150 (0.16) | 74.5 | 0.0990 † | +0.490 (Large) | +1.35 |
| **Deception Rate** | 0.000 (0.00) | 0.000 (0.00) | 50.0 | 1.0000  | +0.000 (Negligible) | +0.00 |
| **Total Water Shared** | 23.600 (2.19) | 9.550 (12.66) | 74.0 | 0.1060  | +0.480 (Large) | +1.55 |
| **Society Gini Coefficient** | 0.453 (0.04) | 0.053 (0.10) | 100.0 | 0.0002 *** | +1.000 (Large) | +5.50 |
| **Society Survival Rate** | 1.000 (0.00) | 0.550 (0.51) | 72.5 | 0.0724 † | +0.450 (Medium) | +1.25 |
| **Focal Survival** | 1.000 (0.00) | 0.550 (0.51) | 72.5 | 0.0724 † | +0.450 (Medium) | +1.25 |
| **Alliance Count** | 1.800 (0.45) | 3.200 (4.48) | 67.5 | 0.2308  | +0.350 (Medium) | -0.44 |
| **Decision Latency (ms)** | 2450.000 (0.00) | 0.000 (0.00) | 100.0 | 0.0000 *** | +1.000 (Large) | +2450000000.00 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Scarcity Dose-Response Elasticity (Novelty N1)

| Group | d(Share)/d(Severity) | d(Hoard)/d(Severity) | Interpretation |
|:------|:--------------------:|:--------------------:|:---------------|
| **Human** | `-0.3093` | `+0.0577` | Shows steep behavioral shifts when scarcity strikes |
| **AI Agent** | `-0.0072` | `-0.0959` | Displays flatter, more rigid behavioral adjustments |

### Camera-Ready LaTeX Table (All Scenarios)

```latex
\begin{table*}[t]
\centering
\caption{Behavioral divergence between human participants and LLM agents under resource scarcity.}
\label{tab:statistical_comparison}
\begin{tabular}{lcccccc}
\toprule
\textbf{Metric} & \textbf{Human Mean (SD)} & \textbf{AI Mean (SD)} & \textbf{Mann-Whitney $U$} & \textbf{$p$-value} & \textbf{Cliff's $\delta$} & \textbf{Cohen's $d$} \\
\midrule
Sharing Rate & 0.094 \small{(0.13)} & 0.158 \small{(0.15)} & 1108.5 & 0.0059$^{\ast\ast}$ & -0.289 & -0.46 \\
Hoarding Rate & 0.037 \small{(0.08)} & 0.090 \small{(0.17)} & 1393.5 & 0.2026 & -0.107 & -0.41 \\
Hoarding Index & 0.557 \small{(0.37)} & 0.206 \small{(0.23)} & 2425.0 & 0.0000$^{\ast\ast\ast}$ & +0.554 & +1.14 \\
Gather Rate & 0.823 \small{(0.25)} & 0.662 \small{(0.28)} & 2210.5 & 0.0001$^{\ast\ast\ast}$ & +0.417 & +0.60 \\
Cooperation Rate & 0.116 \small{(0.16)} & 0.158 \small{(0.15)} & 1215.0 & 0.0354$^{\ast}$ & -0.221 & -0.28 \\
Deception Rate & 0.058 \small{(0.24)} & 0.000 \small{(0.00)} & 1650.0 & 0.0619$^{†}$ & +0.058 & +0.35 \\
Total Water Shared & 3.750 \small{(7.02)} & 5.633 \small{(8.28)} & 1188.0 & 0.0232$^{\ast}$ & -0.238 & -0.25 \\
Society Gini Coefficient & 0.256 \small{(0.14)} & 0.108 \small{(0.16)} & 2400.5 & 0.0000$^{\ast\ast\ast}$ & +0.539 & +1.01 \\
Society Survival Rate & 0.891 \small{(0.30)} & 0.833 \small{(0.38)} & 1595.0 & 0.7522 & +0.022 & +0.17 \\
Focal Survival & 0.885 \small{(0.32)} & 0.717 \small{(0.45)} & 1822.0 & 0.0292$^{\ast}$ & +0.168 & +0.43 \\
Alliance Count & 0.327 \small{(0.68)} & 2.150 \small{(3.18)} & 961.0 & 0.0001$^{\ast\ast\ast}$ & -0.384 & -0.79 \\
Decision Latency (ms) & 1040.777 \small{(1370.64)} & 0.000 \small{(0.00)} & 2880.0 & 0.0000$^{\ast\ast\ast}$ & +0.846 & +1.07 \\
\bottomrule
\multicolumn{7}{l}{\footnotesize{$^\ast p < 0.05$, $^{\ast\ast} p < 0.01$, $^{\ast\ast\ast} p < 0.001$. Two-sided Mann-Whitney $U$ test.}}
\end{tabular}
\end{table*}
```
