# Empirical Statistical Findings: AI vs. Human Behavior Under Scarcity

This report presents the non-parametric hypothesis testing (Mann-Whitney U, Cliff's Delta) and parametric comparisons (Cohen's d, Welch's t-test) across all trials, verifying the behavioral divergence between humans and LLM-driven multi-agent societies.

### All Scenarios (Pooled)

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.168 (0.14) | 0.158 (0.15) | 901.5 | 0.7827  | +0.036 (Negligible) | +0.07 |
| **Hoarding Rate** | 0.067 (0.10) | 0.090 (0.17) | 899.0 | 0.7618  | +0.033 (Negligible) | -0.17 |
| **Hoarding Index** | 0.318 (0.33) | 0.206 (0.23) | 1045.0 | 0.1231  | +0.201 (Small) | +0.39 |
| **Gather Rate** | 0.683 (0.27) | 0.662 (0.28) | 945.5 | 0.5080  | +0.087 (Negligible) | +0.08 |
| **Cooperation Rate** | 0.208 (0.16) | 0.158 (0.15) | 1008.0 | 0.2213  | +0.159 (Small) | +0.33 |
| **Deception Rate** | 0.103 (0.31) | 0.000 (0.00) | 960.0 | 0.0122 * | +0.103 (Negligible) | +0.47 |
| **Total Water Shared** | 6.724 (8.31) | 5.633 (8.28) | 981.0 | 0.3250  | +0.128 (Negligible) | +0.13 |
| **Society Gini Coefficient** | 0.263 (0.18) | 0.108 (0.16) | 1227.5 | 0.0013 ** | +0.411 (Medium) | +0.91 |
| **Society Survival Rate** | 0.805 (0.38) | 0.850 (0.36) | 774.0 | 0.2211  | -0.110 (Negligible) | -0.12 |
| **Focal Survival** | 0.793 (0.41) | 0.717 (0.45) | 936.5 | 0.4461  | +0.076 (Negligible) | +0.18 |
| **Alliance Count** | 0.586 (0.82) | 2.133 (3.19) | 673.5 | 0.0641 † | -0.226 (Small) | -0.66 |
| **Decision Latency (ms)** | 1671.945 (1577.38) | 0.000 (0.00) | 1500.0 | 0.0000 *** | +0.724 (Large) | +1.50 |

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
| **Sharing Rate** | 0.123 (0.16) | 0.155 (0.14) | 156.0 | 0.3313  | -0.179 (Small) | -0.22 |
| **Hoarding Rate** | 0.102 (0.11) | 0.046 (0.11) | 255.5 | 0.0366 * | +0.345 (Medium) | +0.52 |
| **Hoarding Index** | 0.418 (0.38) | 0.294 (0.22) | 222.0 | 0.3697  | +0.168 (Small) | +0.40 |
| **Gather Rate** | 0.684 (0.33) | 0.711 (0.29) | 189.0 | 0.9885  | -0.005 (Negligible) | -0.08 |
| **Cooperation Rate** | 0.149 (0.17) | 0.155 (0.14) | 177.5 | 0.7286  | -0.066 (Negligible) | -0.04 |
| **Deception Rate** | 0.158 (0.37) | 0.000 (0.00) | 220.0 | 0.0726 † | +0.158 (Small) | +0.60 |
| **Total Water Shared** | 2.211 (2.27) | 3.500 (3.49) | 164.0 | 0.4585  | -0.137 (Negligible) | -0.44 |
| **Society Gini Coefficient** | 0.175 (0.17) | 0.124 (0.18) | 215.0 | 0.4778  | +0.132 (Negligible) | +0.30 |
| **Society Survival Rate** | 0.713 (0.44) | 1.000 (0.00) | 120.0 | 0.0034 ** | -0.368 (Medium) | -0.91 |
| **Focal Survival** | 0.684 (0.48) | 0.800 (0.41) | 168.0 | 0.4246  | -0.116 (Negligible) | -0.26 |
| **Alliance Count** | 0.211 (0.54) | 1.400 (1.96) | 110.0 | 0.0090 ** | -0.421 (Medium) | -0.83 |
| **Decision Latency (ms)** | 1262.442 (1832.23) | 0.000 (0.00) | 300.0 | 0.0001 *** | +0.579 (Large) | +0.97 |

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
| **Human** | `-0.2173` | `+0.1396` | Shows steep behavioral shifts when scarcity strikes |
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
Sharing Rate & 0.168 \small{(0.14)} & 0.158 \small{(0.15)} & 901.5 & 0.7827 & +0.036 & +0.07 \\
Hoarding Rate & 0.067 \small{(0.10)} & 0.090 \small{(0.17)} & 899.0 & 0.7618 & +0.033 & -0.17 \\
Hoarding Index & 0.318 \small{(0.33)} & 0.206 \small{(0.23)} & 1045.0 & 0.1231 & +0.201 & +0.39 \\
Gather Rate & 0.683 \small{(0.27)} & 0.662 \small{(0.28)} & 945.5 & 0.5080 & +0.087 & +0.08 \\
Cooperation Rate & 0.208 \small{(0.16)} & 0.158 \small{(0.15)} & 1008.0 & 0.2213 & +0.159 & +0.33 \\
Deception Rate & 0.103 \small{(0.31)} & 0.000 \small{(0.00)} & 960.0 & 0.0122$^{\ast}$ & +0.103 & +0.47 \\
Total Water Shared & 6.724 \small{(8.31)} & 5.633 \small{(8.28)} & 981.0 & 0.3250 & +0.128 & +0.13 \\
Society Gini Coefficient & 0.263 \small{(0.18)} & 0.108 \small{(0.16)} & 1227.5 & 0.0013$^{\ast\ast}$ & +0.411 & +0.91 \\
Society Survival Rate & 0.805 \small{(0.38)} & 0.850 \small{(0.36)} & 774.0 & 0.2211 & -0.110 & -0.12 \\
Focal Survival & 0.793 \small{(0.41)} & 0.717 \small{(0.45)} & 936.5 & 0.4461 & +0.076 & +0.18 \\
Alliance Count & 0.586 \small{(0.82)} & 2.133 \small{(3.19)} & 673.5 & 0.0641$^{†}$ & -0.226 & -0.66 \\
Decision Latency (ms) & 1671.945 \small{(1577.38)} & 0.000 \small{(0.00)} & 1500.0 & 0.0000$^{\ast\ast\ast}$ & +0.724 & +1.50 \\
\bottomrule
\multicolumn{7}{l}{\footnotesize{$^\ast p < 0.05$, $^{\ast\ast} p < 0.01$, $^{\ast\ast\ast} p < 0.001$. Two-sided Mann-Whitney $U$ test.}}
\end{tabular}
\end{table*}
```
