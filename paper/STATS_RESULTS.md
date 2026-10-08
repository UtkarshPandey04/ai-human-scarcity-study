# Empirical Statistical Findings: AI vs. Human Behavior Under Scarcity

This report presents the non-parametric hypothesis testing (Mann-Whitney U, Cliff's Delta) and parametric comparisons (Cohen's d, Welch's t-test) across all trials, verifying the behavioral divergence between humans and LLM-driven multi-agent societies.

### All Scenarios (Pooled)

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.203 (0.13) | 0.158 (0.15) | 856.5 | 0.1729  | +0.190 (Small) | +0.32 |
| **Hoarding Rate** | 0.081 (0.10) | 0.090 (0.17) | 791.5 | 0.4017  | +0.099 (Negligible) | -0.07 |
| **Hoarding Index** | 0.206 (0.24) | 0.206 (0.23) | 745.0 | 0.8063  | +0.035 (Negligible) | -0.00 |
| **Gather Rate** | 0.617 (0.24) | 0.662 (0.28) | 670.5 | 0.6253  | -0.069 (Negligible) | -0.17 |
| **Cooperation Rate** | 0.251 (0.14) | 0.158 (0.15) | 963.0 | 0.0151 * | +0.338 (Medium) | +0.65 |
| **Deception Rate** | 0.125 (0.34) | 0.000 (0.00) | 810.0 | 0.0058 ** | +0.125 (Negligible) | +0.52 |
| **Total Water Shared** | 8.125 (8.49) | 5.633 (8.28) | 936.0 | 0.0306 * | +0.300 (Small) | +0.30 |
| **Society Gini Coefficient** | 0.266 (0.20) | 0.108 (0.16) | 972.5 | 0.0096 ** | +0.351 (Medium) | +0.87 |
| **Society Survival Rate** | 0.765 (0.41) | 0.850 (0.36) | 601.5 | 0.0944 † | -0.165 (Small) | -0.22 |
| **Focal Survival** | 0.750 (0.44) | 0.717 (0.45) | 744.0 | 0.7632  | +0.033 (Negligible) | +0.07 |
| **Alliance Count** | 0.708 (0.86) | 2.133 (3.19) | 606.0 | 0.2302  | -0.158 (Small) | -0.61 |
| **Decision Latency (ms)** | 1759.350 (1409.89) | 0.000 (0.00) | 1200.0 | 0.0000 *** | +0.667 (Large) | +1.76 |

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
| **Sharing Rate** | 0.167 (0.16) | 0.155 (0.14) | 141.0 | 0.9857  | +0.007 (Negligible) | +0.08 |
| **Hoarding Rate** | 0.138 (0.10) | 0.046 (0.11) | 215.5 | 0.0037 ** | +0.539 (Large) | +0.87 |
| **Hoarding Index** | 0.261 (0.31) | 0.294 (0.22) | 122.0 | 0.5337  | -0.129 (Negligible) | -0.12 |
| **Gather Rate** | 0.571 (0.31) | 0.711 (0.29) | 101.5 | 0.1784  | -0.275 (Small) | -0.46 |
| **Cooperation Rate** | 0.202 (0.16) | 0.155 (0.14) | 162.5 | 0.4337  | +0.161 (Small) | +0.32 |
| **Deception Rate** | 0.214 (0.43) | 0.000 (0.00) | 170.0 | 0.0357 * | +0.214 (Small) | +0.71 |
| **Total Water Shared** | 3.000 (2.15) | 3.500 (3.49) | 149.0 | 0.7605  | +0.064 (Negligible) | -0.17 |
| **Society Gini Coefficient** | 0.150 (0.19) | 0.124 (0.18) | 130.0 | 0.7280  | -0.071 (Negligible) | +0.14 |
| **Society Survival Rate** | 0.611 (0.48) | 1.000 (0.00) | 70.0 | 0.0006 *** | -0.500 (Large) | -1.15 |
| **Focal Survival** | 0.571 (0.51) | 0.800 (0.41) | 108.0 | 0.1627  | -0.229 (Small) | -0.49 |
| **Alliance Count** | 0.286 (0.61) | 1.400 (1.96) | 87.5 | 0.0403 * | -0.375 (Medium) | -0.77 |
| **Decision Latency (ms)** | 1266.029 (1699.37) | 0.000 (0.00) | 200.0 | 0.0017 ** | +0.429 (Medium) | +1.05 |

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
| **Human** | `-0.1559` | `+0.1942` | Shows steep behavioral shifts when scarcity strikes |
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
Sharing Rate & 0.203 \small{(0.13)} & 0.158 \small{(0.15)} & 856.5 & 0.1729 & +0.190 & +0.32 \\
Hoarding Rate & 0.081 \small{(0.10)} & 0.090 \small{(0.17)} & 791.5 & 0.4017 & +0.099 & -0.07 \\
Hoarding Index & 0.206 \small{(0.24)} & 0.206 \small{(0.23)} & 745.0 & 0.8063 & +0.035 & -0.00 \\
Gather Rate & 0.617 \small{(0.24)} & 0.662 \small{(0.28)} & 670.5 & 0.6253 & -0.069 & -0.17 \\
Cooperation Rate & 0.251 \small{(0.14)} & 0.158 \small{(0.15)} & 963.0 & 0.0151$^{\ast}$ & +0.338 & +0.65 \\
Deception Rate & 0.125 \small{(0.34)} & 0.000 \small{(0.00)} & 810.0 & 0.0058$^{\ast\ast}$ & +0.125 & +0.52 \\
Total Water Shared & 8.125 \small{(8.49)} & 5.633 \small{(8.28)} & 936.0 & 0.0306$^{\ast}$ & +0.300 & +0.30 \\
Society Gini Coefficient & 0.266 \small{(0.20)} & 0.108 \small{(0.16)} & 972.5 & 0.0096$^{\ast\ast}$ & +0.351 & +0.87 \\
Society Survival Rate & 0.765 \small{(0.41)} & 0.850 \small{(0.36)} & 601.5 & 0.0944$^{†}$ & -0.165 & -0.22 \\
Focal Survival & 0.750 \small{(0.44)} & 0.717 \small{(0.45)} & 744.0 & 0.7632 & +0.033 & +0.07 \\
Alliance Count & 0.708 \small{(0.86)} & 2.133 \small{(3.19)} & 606.0 & 0.2302 & -0.158 & -0.61 \\
Decision Latency (ms) & 1759.350 \small{(1409.89)} & 0.000 \small{(0.00)} & 1200.0 & 0.0000$^{\ast\ast\ast}$ & +0.667 & +1.76 \\
\bottomrule
\multicolumn{7}{l}{\footnotesize{$^\ast p < 0.05$, $^{\ast\ast} p < 0.01$, $^{\ast\ast\ast} p < 0.001$. Two-sided Mann-Whitney $U$ test.}}
\end{tabular}
\end{table*}
```
