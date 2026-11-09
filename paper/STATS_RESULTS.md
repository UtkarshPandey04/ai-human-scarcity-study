# Empirical Statistical Findings: AI vs. Human Behavior Under Scarcity

This report presents the non-parametric hypothesis testing (Mann-Whitney U, Cliff's Delta) and parametric comparisons (Cohen's d, Welch's t-test) across all trials, verifying the behavioral divergence between humans and LLM-driven multi-agent societies.

### All Scenarios (Pooled)

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.154 (0.16) | 0.156 (0.16) | 21771.0 | 0.2262  | -0.070 (Negligible) | -0.01 |
| **Hoarding Rate** | 0.036 (0.06) | 0.109 (0.20) | 21396.5 | 0.0700 † | -0.086 (Negligible) | -0.51 |
| **Hoarding Index** | 0.336 (0.33) | 0.202 (0.23) | 29575.5 | 0.0000 *** | +0.264 (Small) | +0.47 |
| **Gather Rate** | 0.723 (0.22) | 0.659 (0.31) | 26311.5 | 0.0343 * | +0.124 (Negligible) | +0.24 |
| **Cooperation Rate** | 0.232 (0.20) | 0.156 (0.16) | 27897.0 | 0.0009 *** | +0.192 (Small) | +0.41 |
| **Deception Rate** | 0.046 (0.17) | 0.000 (0.00) | 25380.0 | 0.0000 *** | +0.085 (Negligible) | +0.38 |
| **Total Water Shared** | 6.892 (8.96) | 5.128 (7.67) | 23533.5 | 0.9212  | +0.006 (Negligible) | +0.21 |
| **Society Gini Coefficient** | 0.316 (0.13) | 0.058 (0.10) | 43453.0 | 0.0000 *** | +0.857 (Large) | +2.31 |
| **Society Survival Rate** | 0.960 (0.19) | 0.652 (0.48) | 30569.5 | 0.0000 *** | +0.306 (Small) | +0.85 |
| **Focal Survival** | 0.877 (0.33) | 0.614 (0.49) | 29555.0 | 0.0000 *** | +0.263 (Small) | +0.63 |
| **Alliance Count** | 0.677 (0.77) | 1.858 (2.73) | 19477.0 | 0.0026 ** | -0.168 (Small) | -0.59 |
| **Decision Latency (ms)** | 1703.496 (1065.91) | 0.000 (0.00) | 45360.0 | 0.0000 *** | +0.938 (Large) | +2.26 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Calm Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.343 (0.05) | 0.168 (0.17) | 2885.0 | 0.0000 *** | +0.603 (Large) | +1.40 |
| **Hoarding Rate** | 0.000 (0.00) | 0.078 (0.18) | 1425.0 | 0.0067 ** | -0.208 (Small) | -0.61 |
| **Hoarding Index** | 0.130 (0.06) | 0.305 (0.24) | 1266.0 | 0.0115 * | -0.297 (Small) | -0.98 |
| **Gather Rate** | 0.657 (0.05) | 0.679 (0.32) | 1493.5 | 0.1439  | -0.170 (Small) | -0.10 |
| **Cooperation Rate** | 0.343 (0.05) | 0.168 (0.17) | 2885.0 | 0.0000 *** | +0.603 (Large) | +1.40 |
| **Deception Rate** | 0.000 (0.00) | 0.000 (0.00) | 1800.0 | 1.0000  | +0.000 (Negligible) | +0.00 |
| **Total Water Shared** | 10.067 (1.39) | 3.642 (3.84) | 3204.5 | 0.0000 *** | +0.780 (Large) | +2.23 |
| **Society Gini Coefficient** | 0.394 (0.04) | 0.069 (0.11) | 3510.0 | 0.0000 *** | +0.950 (Large) | +4.01 |
| **Society Survival Rate** | 1.000 (0.00) | 0.842 (0.37) | 2085.0 | 0.0203 * | +0.158 (Small) | +0.61 |
| **Focal Survival** | 1.000 (0.00) | 0.767 (0.42) | 2220.0 | 0.0035 ** | +0.233 (Small) | +0.78 |
| **Alliance Count** | 1.000 (0.59) | 1.533 (1.95) | 1900.0 | 0.6238  | +0.056 (Negligible) | -0.37 |
| **Decision Latency (ms)** | 2192.227 (65.69) | 0.000 (0.00) | 3600.0 | 0.0000 *** | +1.000 (Large) | +47.19 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Drought Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.023 (0.09) | 0.156 (0.16) | 1742.5 | 0.0000 *** | -0.585 (Large) | -1.03 |
| **Hoarding Rate** | 0.066 (0.08) | 0.077 (0.18) | 5115.5 | 0.0025 ** | +0.218 (Small) | -0.08 |
| **Hoarding Index** | 0.555 (0.31) | 0.286 (0.22) | 5990.0 | 0.0000 *** | +0.426 (Medium) | +0.99 |
| **Gather Rate** | 0.814 (0.24) | 0.692 (0.32) | 5250.0 | 0.0033 ** | +0.250 (Small) | +0.43 |
| **Cooperation Rate** | 0.102 (0.14) | 0.156 (0.16) | 3206.0 | 0.0047 ** | -0.237 (Small) | -0.36 |
| **Deception Rate** | 0.086 (0.23) | 0.000 (0.00) | 4860.0 | 0.0000 *** | +0.157 (Small) | +0.53 |
| **Total Water Shared** | 0.329 (1.21) | 3.308 (3.32) | 1709.0 | 0.0000 *** | -0.593 (Large) | -1.19 |
| **Society Gini Coefficient** | 0.224 (0.09) | 0.060 (0.10) | 7428.0 | 0.0000 *** | +0.769 (Large) | +1.75 |
| **Society Survival Rate** | 0.925 (0.26) | 0.808 (0.40) | 4656.5 | 0.0454 * | +0.109 (Negligible) | +0.35 |
| **Focal Survival** | 0.871 (0.34) | 0.767 (0.42) | 4640.0 | 0.0797 † | +0.105 (Negligible) | +0.27 |
| **Alliance Count** | 0.143 (0.35) | 1.300 (1.59) | 2255.0 | 0.0000 *** | -0.463 (Medium) | -1.01 |
| **Decision Latency (ms)** | 1282.062 (1314.10) | 0.000 (0.00) | 7920.0 | 0.0000 *** | +0.886 (Large) | +1.38 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Repeated-Trust Condition

| Metric | Human Mean (SD) | AI Mean (SD) | Mann-Whitney U | p-value | Cliff's Delta (Effect) | Cohen's d |
|:-------|:---------------:|:------------:|:--------------:|:-------:|:----------------------:|:---------:|
| **Sharing Rate** | 0.269 (0.02) | 0.145 (0.17) | 2479.5 | 0.0012 ** | +0.378 (Medium) | +1.05 |
| **Hoarding Rate** | 0.000 (0.00) | 0.173 (0.21) | 975.0 | 0.0000 *** | -0.458 (Medium) | -1.15 |
| **Hoarding Index** | 0.034 (0.03) | 0.016 (0.03) | 2524.5 | 0.0001 *** | +0.403 (Medium) | +0.65 |
| **Gather Rate** | 0.577 (0.18) | 0.606 (0.28) | 2008.0 | 0.3253  | +0.116 (Negligible) | -0.12 |
| **Cooperation Rate** | 0.423 (0.18) | 0.145 (0.17) | 2972.0 | 0.0000 *** | +0.651 (Large) | +1.58 |
| **Deception Rate** | 0.000 (0.00) | 0.000 (0.00) | 1800.0 | 1.0000  | +0.000 (Negligible) | +0.00 |
| **Total Water Shared** | 19.033 (9.19) | 8.433 (11.62) | 2623.0 | 0.0001 *** | +0.457 (Medium) | +1.01 |
| **Society Gini Coefficient** | 0.454 (0.05) | 0.044 (0.08) | 3591.0 | 0.0000 *** | +0.995 (Large) | +5.96 |
| **Society Survival Rate** | 1.000 (0.00) | 0.307 (0.46) | 3060.0 | 0.0000 *** | +0.700 (Large) | +2.12 |
| **Focal Survival** | 0.767 (0.43) | 0.308 (0.46) | 2625.0 | 0.0000 *** | +0.458 (Medium) | +1.02 |
| **Alliance Count** | 1.600 (0.56) | 2.742 (3.86) | 2293.0 | 0.0164 * | +0.274 (Small) | -0.41 |
| **Decision Latency (ms)** | 2198.111 (109.60) | 0.000 (0.00) | 3600.0 | 0.0000 *** | +1.000 (Large) | +28.36 |

*Significance: † p < 0.1, * p < 0.05, ** p < 0.01, *** p < 0.001.*

### Scarcity Dose-Response Elasticity (Novelty N1)

| Group | d(Share)/d(Severity) | d(Hoard)/d(Severity) | Interpretation |
|:------|:--------------------:|:--------------------:|:---------------|
| **Human** | `-0.4123` | `+0.0930` | Shows steep behavioral shifts when scarcity strikes |
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
Sharing Rate & 0.154 \small{(0.16)} & 0.156 \small{(0.16)} & 21771.0 & 0.2262 & -0.070 & -0.01 \\
Hoarding Rate & 0.036 \small{(0.06)} & 0.109 \small{(0.20)} & 21396.5 & 0.0700$^{†}$ & -0.086 & -0.51 \\
Hoarding Index & 0.336 \small{(0.33)} & 0.202 \small{(0.23)} & 29575.5 & 0.0000$^{\ast\ast\ast}$ & +0.264 & +0.47 \\
Gather Rate & 0.723 \small{(0.22)} & 0.659 \small{(0.31)} & 26311.5 & 0.0343$^{\ast}$ & +0.124 & +0.24 \\
Cooperation Rate & 0.232 \small{(0.20)} & 0.156 \small{(0.16)} & 27897.0 & 0.0009$^{\ast\ast\ast}$ & +0.192 & +0.41 \\
Deception Rate & 0.046 \small{(0.17)} & 0.000 \small{(0.00)} & 25380.0 & 0.0000$^{\ast\ast\ast}$ & +0.085 & +0.38 \\
Total Water Shared & 6.892 \small{(8.96)} & 5.128 \small{(7.67)} & 23533.5 & 0.9212 & +0.006 & +0.21 \\
Society Gini Coefficient & 0.316 \small{(0.13)} & 0.058 \small{(0.10)} & 43453.0 & 0.0000$^{\ast\ast\ast}$ & +0.857 & +2.31 \\
Society Survival Rate & 0.960 \small{(0.19)} & 0.652 \small{(0.48)} & 30569.5 & 0.0000$^{\ast\ast\ast}$ & +0.306 & +0.85 \\
Focal Survival & 0.877 \small{(0.33)} & 0.614 \small{(0.49)} & 29555.0 & 0.0000$^{\ast\ast\ast}$ & +0.263 & +0.63 \\
Alliance Count & 0.677 \small{(0.77)} & 1.858 \small{(2.73)} & 19477.0 & 0.0026$^{\ast\ast}$ & -0.168 & -0.59 \\
Decision Latency (ms) & 1703.496 \small{(1065.91)} & 0.000 \small{(0.00)} & 45360.0 & 0.0000$^{\ast\ast\ast}$ & +0.938 & +2.26 \\
\bottomrule
\multicolumn{7}{l}{\footnotesize{$^\ast p < 0.05$, $^{\ast\ast} p < 0.01$, $^{\ast\ast\ast} p < 0.001$. Two-sided Mann-Whitney $U$ test.}}
\end{tabular}
\end{table*}
```
