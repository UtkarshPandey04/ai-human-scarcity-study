# Empirical Statistical Findings: AI vs. Human Behavior Under Scarcity

This report presents the non-parametric hypothesis testing (Mann-Whitney U, Cliff's Delta) and parametric comparisons (Cohen's d, Welch's t-test) across all trials, verifying the behavioral divergence between humans and LLM-driven multi-agent societies.

### All Scenarios (Pooled)

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.148 (0.15) | 0.156 (0.16) | 21867.0 | 0.2558  | -0.066 (Negligible) | -0.05 |
| **Hoarding Rate** | 0.034 (0.06) | 0.109 (0.20) | 21363.5 | 0.0655 † | -0.087 (Negligible) | -0.52 |
| **Hoarding Index** | 0.372 (0.31) | 0.202 (0.23) | 32365.5 | 0.0000 *** | +0.383 (Medium) | +0.62 |
| **Gather Rate** | 0.770 (0.18) | 0.659 (0.31) | 28729.0 | 0.0001 *** | +0.228 (Small) | +0.44 |
| **Cooperation Rate** | 0.186 (0.14) | 0.156 (0.16) | 25779.0 | 0.0801 † | +0.102 (Negligible) | +0.19 |
| **Deception Rate** | 0.042 (0.18) | 0.000 (0.00) | 24840.0 | 0.0000 *** | +0.062 (Negligible) | +0.34 |
| **Total Water Shared** | 7.262 (8.32) | 5.128 (7.67) | 24920.5 | 0.2595  | +0.065 (Negligible) | +0.27 |
| **Society Gini Coefficient** | 0.309 (0.12) | 0.058 (0.10) | 43377.0 | 0.0000 *** | +0.854 (Large) | +2.32 |
| **Society Survival Rate** | 0.957 (0.19) | 0.652 (0.48) | 30334.5 | 0.0000 *** | +0.296 (Small) | +0.84 |
| **Focal Survival** | 0.954 (0.21) | 0.614 (0.49) | 31355.0 | 0.0000 *** | +0.340 (Medium) | +0.91 |
| **Alliance Count** | 0.754 (0.81) | 1.858 (2.73) | 20290.0 | 0.0172 * | -0.133 (Negligible) | -0.55 |
| **Decision Latency (ms)** | 1649.243 (1037.53) | 0.000 (0.00) | 45360.0 | 0.0000 *** | +0.938 (Large) | +2.25 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Calm Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.323 (0.06) | 0.168 (0.17) | 2793.5 | 0.0000 *** | +0.552 (Large) | +1.21 |
| **Hoarding Rate** | 0.000 (0.00) | 0.078 (0.18) | 1425.0 | 0.0067 ** | -0.208 (Small) | -0.61 |
| **Hoarding Index** | 0.143 (0.06) | 0.305 (0.24) | 1337.5 | 0.0286 * | -0.257 (Small) | -0.91 |
| **Gather Rate** | 0.660 (0.05) | 0.679 (0.32) | 1509.0 | 0.1654  | -0.162 (Small) | -0.08 |
| **Cooperation Rate** | 0.340 (0.05) | 0.168 (0.17) | 2865.0 | 0.0000 *** | +0.592 (Large) | +1.37 |
| **Deception Rate** | 0.000 (0.00) | 0.000 (0.00) | 1800.0 | 1.0000  | +0.000 (Negligible) | +0.00 |
| **Total Water Shared** | 9.467 (1.76) | 3.642 (3.84) | 3107.5 | 0.0000 *** | +0.726 (Large) | +1.95 |
| **Society Gini Coefficient** | 0.391 (0.04) | 0.069 (0.11) | 3510.0 | 0.0000 *** | +0.950 (Large) | +3.97 |
| **Society Survival Rate** | 0.993 (0.04) | 0.842 (0.37) | 2034.5 | 0.0620 † | +0.130 (Negligible) | +0.58 |
| **Focal Survival** | 1.000 (0.00) | 0.767 (0.42) | 2220.0 | 0.0035 ** | +0.233 (Small) | +0.78 |
| **Alliance Count** | 1.033 (0.61) | 1.533 (1.95) | 1918.0 | 0.5628  | +0.066 (Negligible) | -0.35 |
| **Decision Latency (ms)** | 2164.813 (151.58) | 0.000 (0.00) | 3600.0 | 0.0000 *** | +1.000 (Large) | +20.20 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Drought Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.033 (0.10) | 0.156 (0.16) | 1955.0 | 0.0000 *** | -0.535 (Large) | -0.94 |
| **Hoarding Rate** | 0.063 (0.07) | 0.077 (0.18) | 5103.5 | 0.0028 ** | +0.215 (Small) | -0.10 |
| **Hoarding Index** | 0.574 (0.29) | 0.286 (0.22) | 6095.0 | 0.0000 *** | +0.451 (Medium) | +1.11 |
| **Gather Rate** | 0.836 (0.22) | 0.692 (0.32) | 5389.0 | 0.0009 *** | +0.283 (Small) | +0.53 |
| **Cooperation Rate** | 0.083 (0.11) | 0.156 (0.16) | 3002.5 | 0.0007 *** | -0.285 (Small) | -0.54 |
| **Deception Rate** | 0.079 (0.24) | 0.000 (0.00) | 4680.0 | 0.0002 *** | +0.114 (Negligible) | +0.47 |
| **Total Water Shared** | 0.600 (1.53) | 3.308 (3.32) | 1995.0 | 0.0000 *** | -0.525 (Large) | -1.05 |
| **Society Gini Coefficient** | 0.223 (0.09) | 0.060 (0.10) | 7419.0 | 0.0000 *** | +0.766 (Large) | +1.71 |
| **Society Survival Rate** | 0.922 (0.26) | 0.808 (0.40) | 4608.0 | 0.0779 † | +0.097 (Negligible) | +0.34 |
| **Focal Survival** | 0.914 (0.28) | 0.767 (0.42) | 4820.0 | 0.0107 * | +0.148 (Small) | +0.41 |
| **Alliance Count** | 0.200 (0.44) | 1.300 (1.59) | 2395.5 | 0.0000 *** | -0.430 (Medium) | -0.95 |
| **Decision Latency (ms)** | 1222.656 (1261.98) | 0.000 (0.00) | 7920.0 | 0.0000 *** | +0.886 (Large) | +1.37 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Repeated-Trust Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.239 (0.02) | 0.145 (0.17) | 2412.5 | 0.0035 ** | +0.340 (Medium) | +0.79 |
| **Hoarding Rate** | 0.000 (0.00) | 0.173 (0.21) | 975.0 | 0.0000 *** | -0.458 (Medium) | -1.15 |
| **Hoarding Index** | 0.130 (0.03) | 0.016 (0.03) | 3546.0 | 0.0000 *** | +0.970 (Large) | +3.85 |
| **Gather Rate** | 0.728 (0.02) | 0.606 (0.28) | 2700.0 | 0.0000 *** | +0.500 (Large) | +0.61 |
| **Cooperation Rate** | 0.272 (0.02) | 0.145 (0.17) | 2496.5 | 0.0009 *** | +0.387 (Medium) | +1.07 |
| **Deception Rate** | 0.000 (0.00) | 0.000 (0.00) | 1800.0 | 1.0000  | +0.000 (Negligible) | +0.00 |
| **Total Water Shared** | 20.600 (1.81) | 8.433 (11.62) | 2682.0 | 0.0000 *** | +0.490 (Large) | +1.46 |
| **Society Gini Coefficient** | 0.424 (0.03) | 0.044 (0.08) | 3575.0 | 0.0000 *** | +0.986 (Large) | +6.02 |
| **Society Survival Rate** | 1.000 (0.00) | 0.307 (0.46) | 3060.0 | 0.0000 *** | +0.700 (Large) | +2.12 |
| **Focal Survival** | 1.000 (0.00) | 0.308 (0.46) | 3045.0 | 0.0000 *** | +0.692 (Large) | +2.11 |
| **Alliance Count** | 1.767 (0.43) | 2.742 (3.86) | 2401.0 | 0.0035 ** | +0.334 (Medium) | -0.35 |
| **Decision Latency (ms)** | 2129.044 (154.10) | 0.000 (0.00) | 3600.0 | 0.0000 *** | +1.000 (Large) | +19.54 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Scarcity Dose-Response Elasticity (Novelty N1)

| Group | d(Share)/d(Severity) | d(Hoard)/d(Severity) | Interpretation |
|:------|:--------------------:|:--------------------:|:---------------|
| **Human** | `-0.3617` | `+0.0889` | Shows steep behavioral shifts when scarcity strikes |
| **AI Agent** | `-0.0003` | `-0.0696` | Displays flatter, more rigid behavioral adjustments |

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
Sharing Rate & 0.148 \small{(0.15)} & 0.156 \small{(0.16)} & 21867.0 & 0.2558 & -0.066 & -0.05 \\
Hoarding Rate & 0.034 \small{(0.06)} & 0.109 \small{(0.20)} & 21363.5 & 0.0655$^{†}$ & -0.087 & -0.52 \\
Hoarding Index & 0.372 \small{(0.31)} & 0.202 \small{(0.23)} & 32365.5 & 0.0000$^{\ast\ast\ast}$ & +0.383 & +0.62 \\
Gather Rate & 0.770 \small{(0.18)} & 0.659 \small{(0.31)} & 28729.0 & 0.0001$^{\ast\ast\ast}$ & +0.228 & +0.44 \\
Cooperation Rate & 0.186 \small{(0.14)} & 0.156 \small{(0.16)} & 25779.0 & 0.0801$^{†}$ & +0.102 & +0.19 \\
Deception Rate & 0.042 \small{(0.18)} & 0.000 \small{(0.00)} & 24840.0 & 0.0000$^{\ast\ast\ast}$ & +0.062 & +0.34 \\
Total Water Shared & 7.262 \small{(8.32)} & 5.128 \small{(7.67)} & 24920.5 & 0.2595 & +0.065 & +0.27 \\
Society Gini Coefficient & 0.309 \small{(0.12)} & 0.058 \small{(0.10)} & 43377.0 & 0.0000$^{\ast\ast\ast}$ & +0.854 & +2.32 \\
Society Survival Rate & 0.957 \small{(0.19)} & 0.652 \small{(0.48)} & 30334.5 & 0.0000$^{\ast\ast\ast}$ & +0.296 & +0.84 \\
Focal Survival & 0.954 \small{(0.21)} & 0.614 \small{(0.49)} & 31355.0 & 0.0000$^{\ast\ast\ast}$ & +0.340 & +0.91 \\
Alliance Count & 0.754 \small{(0.81)} & 1.858 \small{(2.73)} & 20290.0 & 0.0172$^{\ast}$ & -0.133 & -0.55 \\
Decision Latency (ms) & 1649.243 \small{(1037.53)} & 0.000 \small{(0.00)} & 45360.0 & 0.0000$^{\ast\ast\ast}$ & +0.938 & +2.25 \\
\bottomrule
\multicolumn{7}{l}{\footnotesize{$^\ast p < 0.05$, $^{\ast\ast} p < 0.01$, $^{\ast\ast\ast} p < 0.001$. Two-sided Mann-Whitney $U$ test.}}
\end{tabular}
\end{table*}
```
